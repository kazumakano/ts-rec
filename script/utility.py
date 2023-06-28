import csv
import os.path as path
from datetime import datetime, timedelta
import cv2
import numpy as np
import torch
import yaml
from scipy.special import softmax
from torchvision.transforms import functional as TF


def aug_by_translation(img: torch.Tensor, aug_num: int, max_shift_len: int) -> torch.Tensor:
    """
    Augment image of timestamp figure by randomly translation.

    Parameters
    ----------
    img : Tensor
        Original image.
        Shape is (channel, height, width).
    aug_num : int
        The number of images to augment.
    max_shift_len : int
        Maximum length to shift image.

    Returns
    -------
    imgs : Tensor
        Translated images.
        Shape is (aug_num, channel, height, width).
    """

    translated_imgs = torch.empty((aug_num, 3, 22, 17), dtype=torch.float32)
    for i in range(aug_num):
        translated_imgs[i] = TF.affine(img, 0, np.random.randint(-max_shift_len, high=max_shift_len, size=2).tolist(), 1, 0)

    return translated_imgs

def calc_ts_from_name(file: str, sec_per_file: float = 1791) -> timedelta:
    """
    Roughly calculate timestamp based on video file name.

    Parameters
    ----------
    file : str
        Path to video file.
    sec_per_file : float
        Typical video length [s].

    Returns
    ------
    ts : timedelta
        Timestamp at the start of video.
    """

    return timedelta(seconds=int(file[-9:-7]) + sec_per_file * int(file[-6:-4]), minutes=int(file[-12:-10]), hours=int(file[-15:-13]))

def extract_ts_fig(frm: np.ndarray) -> np.ndarray:
    """
    Extract images of timestamp figures on video frame.

    Parameters
    ----------
    frm : ndarray
        Frame image to extract.
        Shape is (height, width, channel).

    Returns
    -------
    imgs : ndarray
        Images of every timestamp figure.
        Shape is (6, height, width, channel).
    """

    ts_fig_imgs = np.empty((6, 22, 17, 3), dtype=np.uint8)
    for i, digit in enumerate((0, 1, 3, 4, 6, 7)):
        ts_fig_imgs[i] = frm[19:41, 18 * digit + 198:18 * digit + 215]

    return ts_fig_imgs

def get_result_dir(dir_name: str | None) -> str:
    if dir_name is None:
        dir_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    return path.join(path.dirname(__file__), "../result/", dir_name)

def load_param(file: str) -> dict[str, int | list[int] | list[str]]:
    with open(file) as f:
        return yaml.safe_load(f)

def read_1st_frm(file: str) -> np.ndarray:
    return cv2.VideoCapture(filename=file).read()[1]

def write_predict_result(cam_name: np.ndarray, vid_idx: np.ndarray, ts: np.ndarray, result_dir: str) -> None:
    ts = softmax(ts, axis=2).argmax(axis=2)

    with open(path.join(result_dir, "predict_results.csv"), mode="w") as f:
        writer = csv.writer(f)

        for i in range(len(cam_name)):
            writer.writerow((cam_name[i], vid_idx[i], f"{ts[i, 0]}{ts[i, 1]}:{ts[i, 2]}{ts[i, 3]}:{ts[i, 4]}{ts[i, 5]}"))
