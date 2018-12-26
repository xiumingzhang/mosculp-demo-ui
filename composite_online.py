# pylint: disable=W0621

from sys import stdout
from os import makedirs
from os.path import join, exists, dirname
from urllib import FancyURLopener
from time import time
import numpy as np
from PIL import Image
from scipy.ndimage.filters import gaussian_filter
from app_config import web_root, tmp_root


class FileNotOnServerException(Exception):
    pass


class MyURLopener(FancyURLopener):
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        raise FileNotOnServerException(url)

    def lazy_retrieve(self, remote_f, local_f):
        if not exists(local_f):
            print("Downloading to %s" % local_f)
            local_dir = dirname(local_f)
            if not exists(local_dir):
                makedirs(local_dir)
            self.retrieve(remote_f, local_f, self.report_hook)
        else:
            print("%s already exists -- download skipped" % local_f)

    @staticmethod
    def report_hook(count, block_size, total_size):
        global start_time
        if count == 0:
            start_time = time()
            return
        duration = time() - start_time
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = int(count * block_size * 100 / total_size)
        stdout.write("\rProgress: %d%% (%dMB) @ %dKB/s. Time elapsed: %ds. " %
                     (percent, progress_size / (1024 * 1024), speed, duration))
        stdout.flush()


def download_load_idxmaps(req, web_root, tmp_root):
    folder = join(req['clip'], 'composite_enum_idxmap_for-ui-resp')
    local_dir = join(tmp_root, folder)
    if not exists(local_dir):
        makedirs(local_dir)
    f = join(folder, 'density.%.2f_part.%s.npz' %
             (req['density'], '-'.join(sorted(req['part']))))
    remote_f = join(web_root, f)
    local_f = join(tmp_root, f)
    MyURLopener().lazy_retrieve(remote_f, local_f)
    precomp = dict(np.load(local_f))
    precomp['idx_names'] = list(precomp['idx_names'])
    return precomp


def download_load_imgs(req, precomp, web_root, tmp_root):
    # Load frames
    imgs = {}
    for idx_name in precomp['idx_names']:
        if 'sculp_' in idx_name:
            part_name = idx_name.replace('sculp_', '')

            folder = join(
                req['clip'],
                'render_enum_for-ui-resp',
                'part.%s_mat.%s_spec.%s_transp.0.00' % (
                    part_name, req['mat'][part_name], 'On' if req['spec'] else 'Off'),
                'lights.%s_density.%.2f.blend' % (
                    '-'.join(sorted(req['lights'])), req['density']),
            )
            if not exists(join(tmp_root, folder)):
                makedirs(join(tmp_root, folder))

            # Load sculpture RGB
            remote_f = join(web_root, folder, 'sculp_rgb.jpg')
            local_f = join(tmp_root, folder, 'sculp_rgb.jpg')
            MyURLopener().lazy_retrieve(remote_f, local_f)
            imgs[idx_name] = np.array(Image.open(local_f))

            # Load backgrounds
            remote_f = join(web_root, folder, 'shadowbg.jpg')
            local_f = join(tmp_root, folder, 'shadowbg.jpg')
            MyURLopener().lazy_retrieve(remote_f, local_f)
            imgs['bg_' + part_name] = np.array(Image.open(local_f))
            # remote_f = join(web_root, folder, 'shadowbg_bwall.jpg')
            # local_f = join(tmp_root, folder, 'shadowbg_bwall.jpg')
            # MyURLopener().lazy_retrieve(remote_f, local_f)
            # imgs['bg_bwall_' + part_name] = np.array(Image.open(local_f))

        else:
            # Load frames
            remote_f = join(web_root, req['clip'], 'frames_for-ui-resp', idx_name + '.jpg')
            local_dir = join(tmp_root, req['clip'], 'frames_for-ui-resp')
            local_f = join(local_dir, idx_name + '.jpg')
            if not exists(local_dir):
                makedirs(local_dir)
            MyURLopener().lazy_retrieve(remote_f, local_f)
            imgs[idx_name] = np.array(Image.open(local_f))

    return imgs


def combine_shadow(imgs):
    bg_rgbs = []
    # bg_bwall_rgbs = []
    for key, img in imgs.iteritems():
        if key.startswith('bg_'):
            bg_rgbs.append(img)
        # elif key.startswith('bg_bwall_'):
        #    bg_bwall_rgbs.append(img)
    bg_rgbs = np.stack(bg_rgbs, axis=3)
    # bg_bwall_rgbs = np.stack(bg_bwall_rgbs, axis=3)
    bg_rgb = np.mean(bg_rgbs, axis=3)
    # bg_bwall_rgb = np.mean(bg_bwall_rgbs, axis=3)
    imgs = {k: v for k, v in imgs.iteritems() if not k.startswith('bg_')}
    imgs['bg'] = bg_rgb
    # imgs['bg_bwall'] = bg_bwall_rgb
    return imgs


def simple_matting(imgs, prev_idx_map, curr_idx_map, idx_names, sculp_transp, kernel_size):
    # Generate nImgs-by-h-by-w cube for blending the human images
    is_sculp = np.zeros(curr_idx_map.shape, dtype=bool)
    for i, idx_name in enumerate(idx_names):
        if idx_name.startswith('sculp_'):
            is_sculp = np.logical_or(is_sculp, curr_idx_map == i)
    w_cube, img_cube = [], []
    for i, idx_name in enumerate(idx_names):
        if idx_name.startswith('sculp'):
            w_map = (1 - sculp_transp) * (curr_idx_map == i).astype('double')
        else:
            w_map = (curr_idx_map == i).astype('double')
            w_map[np.logical_and(is_sculp, prev_idx_map == i)] = sculp_transp
        w_map = gaussian_filter(w_map, kernel_size) # sigma is 0.3*((ksize-1)*0.5-1)+0.8
        w_cube.append(w_map)
        img_cube.append(imgs[idx_name])
        img_shape = imgs[idx_name].shape
    w_cube = np.stack(w_cube, axis=2)
    img_cube = np.stack(img_cube, axis=3)
    # Normalize
    w_sum = np.sum(w_cube, axis=2)
    w_cube = np.true_divide(w_cube, np.repeat(w_sum[..., np.newaxis], w_cube.shape[2], axis=2))
    # Composite
    comp = np.zeros(img_shape)
    for c in range(3):
        comp[:, :, c] = np.sum(np.multiply(w_cube, img_cube[:, :, c, :]), axis=2)
    return comp


def composite(imgs, fgmask, precomp, sculp_transp, artistic_bg):
    kernel_size = 1.5 # for simple matting

    prev_idx_map = precomp['prev_idx_map']
    curr_idx_map = precomp['curr_idx_map']
    idx_names = precomp['idx_names']

    if artistic_bg:
        # Composite with black, syntheic background
        bg_str = 'bg' # 'bg_bwall'
        idx_names.append(bg_str)
        bg_idx = len(idx_names) - 1
        h, w = curr_idx_map.shape
        # Pad
        bg = imgs[bg_str]
        if (h, w) != bg.shape[:2]:
            n_vpad, n_hpad = h, w
            n_tpad, n_lpad = n_vpad // 2, n_hpad // 2
            n_bpad, n_rpad = n_vpad - n_tpad, n_hpad - n_lpad
        else:
            n_tpad = n_bpad = n_lpad = n_rpad = 0
        imgs_2x = {
            k: np.pad(v, ((n_tpad, n_bpad),
                          (n_lpad, n_rpad),
                          (0, 0)), 'constant', constant_values=0)
            for k, v in imgs.iteritems() if not k.startswith('bg')
        }
        imgs_2x[bg_str] = imgs[bg_str]
        fgmask_2x = np.pad(fgmask, ((n_tpad, n_bpad), (n_lpad, n_rpad)),
                           'constant', constant_values=False)
        curr_idx_map_2x = np.ones(fgmask_2x.shape) * bg_idx
        curr_idx_map_2x[fgmask_2x] = curr_idx_map[fgmask]
        prev_idx_map_2x = np.ones(fgmask_2x.shape) * bg_idx
        framenames = sorted(k for k in imgs.keys() if 'sculp' not in k and 'bg' not in k)
        prev_idx_map[prev_idx_map == idx_names.index(framenames[-1])] = bg_idx
        prev_idx_map_2x[fgmask_2x] = prev_idx_map[fgmask]
        #
        comp = simple_matting(
            imgs_2x,
            prev_idx_map_2x,
            curr_idx_map_2x,
            idx_names,
            sculp_transp,
            kernel_size,
        )
    else:
        # Composite with the original video
        comp = simple_matting(
            imgs,
            prev_idx_map,
            curr_idx_map,
            idx_names,
            sculp_transp,
            kernel_size,
        )

    return comp


def get_req_str(req):
    req_str = ''
    for k, v in req.iteritems():
        if isinstance(v, str):
            req_str += '%s.%s_' % (k, v)
        elif isinstance(v, list):
            req_str += '%s.%s_' % (k, '-'.join(sorted(v)))
        elif isinstance(v, (int, float)):
            req_str += '%s.%.2f_' % (k, v)
        elif isinstance(v, dict):
            req_str += '%s.%s_' % (k, '-'.join(v[x] for x in sorted(req['part'])))
        else:
            raise TypeError(v)
    return req_str[:-1]


def main(req, artistic_bg, cache=True):
    req['part'] = [x.replace(' ', '') for x in req['part']]
    for k, v in req['mat'].iteritems():
        if v == 'Original':
            req['mat'][k] = 'Orig'

    cache_dir = join(tmp_root, req['clip'], 'composite_enum',
                     get_req_str(req).replace('_', '/'))
    if artistic_bg:
        comp_f = join(cache_dir, 'comp_2x.png') # 2x is legacy, just meaning arbitrary size
    else:
        comp_f = join(cache_dir, 'comp.png')

    # Results are cached, so directly return
    if cache and exists(comp_f):
        print("------ Combination Cached ------")
        return comp_f

    print("********** Combination New **********")

    # Download and then load the precomputed index maps
    print("* Downloading precomputed index maps...")
    t0 = time()
    precomp = download_load_idxmaps(req, web_root, tmp_root)
    print("Done in %fs" % (time() - t0))

    # Download and then load image ingredients
    print("* Downloading image ingradients...")
    t0 = time()
    imgs = download_load_imgs(req, precomp, web_root, tmp_root)
    print("Done in %fs" % (time() - t0))

    # Combine backgrounds
    print("* Combining backgrounds with shadow...")
    t0 = time()
    imgs = combine_shadow(imgs)
    print("Done in %fs" % (time() - t0))

    # Composite
    print("* Compositing...")
    t0 = time()
    comp = composite(imgs, precomp['is_fg'], precomp, req['transp'], artistic_bg)
    print("Done in %fs" % (time() - t0))

    print("*************************************")

    # Clip-dependent cropping
    if req['clip'] == 'ballet11-2':
        comp = comp[50:, 350:1160, :]
    elif req['clip'] == 'olympicRunning_cut':
        comp = comp[:, 300:1600, :]

    # Write to disk
    if not exists(cache_dir):
        makedirs(cache_dir)
    Image.fromarray(comp.astype(np.uint8)).save(comp_f)

    return comp_f


if __name__ == '__main__':
    main(
        {
            'clip': 'ballet11-2',
            'density': 0,
            'lights': ['Left', 'Middle', 'Right'],
            'transp': 0,
            'spec': True,
            'part': ['Body', 'LeftUpperArm'],
            'mat': {'Body': 'Leather', 'LeftUpperArm': 'Tarp'},
        },
        True,
    )
