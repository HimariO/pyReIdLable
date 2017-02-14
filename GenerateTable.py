import scipy.io as sio
from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy
import math
import argparse
from progress.bar import Bar


class ProgressBar(Bar):
    message = 'Loading'
    fill = '#'
    suffix = '%(percent).1f%% | ETA: %(eta)ds'


parser = argparse.ArgumentParser()

parser.add_argument("-v", "--video", help="video file name")
parser.add_argument("-a", "--anno", help="annotation file name")
parser.add_argument("-t", "--testing", help="testing run, only process 1000 frames max.")
parser.add_argument("-ns", "--notSaving", help="wont save the result_img(this arg is for using with ipython)")

args = parser.parse_args()

fileName = args.anno

mat_to_list = lambda mat: [(field, getattr(mat, field)) for field in mat._fieldnames]
get_box = lambda posMeb: (int(posMeb[0]), int(posMeb[1]), int(posMeb[2]) + int(posMeb[0]), int(posMeb[3]) + int(posMeb[1]))


def sort_crop(img_list, max_num=20):
    if len(img_list) > max_num:
        step = math.floor(len(img_list) / 9)
        picked = img_list[::step]
        return picked
    else:
        return img_list


clip = VideoFileClip(args.video)
vbb = sio.loadmat(fileName, squeeze_me=True, struct_as_record=False)
vbb_A = vbb['A']

params = mat_to_list(vbb_A)

objList = params[1][1]
objLable = [n for n in params[4][1]]  # still can find duplicated lable in this list. but need those to map objectID to Lable(name).
obj_img_dic = {}

for lab in objLable:
    obj_img_dic[lab] = []

max_width = 0
max_height = 0
bar = ProgressBar(args.video, max=len(objList))

for frame, i in zip(clip.iter_frames(), range(len(objList))):
    if i > 1000 and args.testing == 'true':
        break
    frame_slot = objList[i]
    img = Image.fromarray(frame)

    if type(frame_slot) == numpy.ndarray:
        if frame_slot.size > 0:  # if slot cotain more than one boxpos or no data it will be ndarray.
            for m in frame_slot:
                box = img.crop(get_box(m.pos))
                ind = int(m.id) - 1
                obj_img_dic[objLable[ind]].append(box)
                obj_img_dic[objLable[ind]] = sort_crop(obj_img_dic[objLable[ind]])

                if m.pos[2] > max_width:
                    max_width = m.pos[2]
                if m.pos[3] > max_height:
                    max_height = m.pos[3]

    else:  # else it will be matstruct object.
        box = img.crop(get_box(frame_slot.pos))
        ind = int(frame_slot.id) - 1
        obj_img_dic[objLable[ind]].append(box)
        obj_img_dic[objLable[ind]] = sort_crop(obj_img_dic[objLable[ind]])

        if frame_slot.pos[3] > max_height:
            max_height = frame_slot.pos[3]
        if frame_slot.pos[2] > max_width:
            max_width = frame_slot.pos[2]

    bar.next()

bar.finish()

if args.notSaving != 'true':
    max_width = int(max_width)
    max_height = int(max_height)

    result_img_size = (5, math.ceil(len(obj_img_dic.keys()) / 5))  # col, row
    result_img = Image.new('RGB', (result_img_size[0] * max_width, result_img_size[1] * max_height))
    fon = ImageFont.truetype("FreeMono.ttf", 20)
    draw = ImageDraw.Draw(result_img)

    for ID, i in zip(obj_img_dic.keys(), range(len(obj_img_dic.keys()))):
        img_list = obj_img_dic[ID]

        try:
            picked = img_list[math.floor(len(img_list) / 2)]

            col = i % result_img_size[0]
            row = math.floor(i / result_img_size[0])
            result_img.paste(picked.resize((max_width, max_height)), (col * max_width, row * max_height))
            draw.text((col * max_width, row * max_height), str(ID), font=fon, fill=(255, 255, 255))
        except:
            break

    result_img_title = Image.new('RGB', (result_img_size[0] * max_width, result_img_size[1] * max_height + 50))
    fon = ImageFont.truetype("FreeMono.ttf", 45)
    draw = ImageDraw.Draw(result_img_title)

    draw.text((10, 5), args.video, font=fon, fill=(255, 255, 255))
    result_img_title.paste(result_img, (0, 50))

    result_img_title.save(args.anno[:-4].split('/')[-1] + '_sheet.jpg')
