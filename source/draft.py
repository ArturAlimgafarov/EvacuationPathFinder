from tkinter import *
from config import *
from tkinter.filedialog import askopenfile
from PIL import ImageTk, Image
import cv2
import numpy as np

window = Tk()
window.title('AUTOMATIC')
window.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
window.resizable(False, False)

canvas = Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
canvas.place(x=CANVAS_OFFSET_X, y=CANVAS_OFFSET_Y)

file = askopenfile(filetypes=(('PNG', '*png'), ('JPEG', '*jpeg *jpg'), ('All Files', '*.*')))
image = np.asarray(Image.open(file.name))
h, w = image.shape[:2]
k = CANVAS_WIDTH / w if w > h else CANVAS_HEIGHT / h
h, w = int(h * k), int(w * k)
image = cv2.resize(image, (w, h))
B, G, R = cv2.split(image)[:3] # get color channels as lists
alpha = 100 # transparency value
A = np.ones(B.shape, dtype=B.dtype) * alpha # image alpha-channel as list
image = cv2.merge((R, G, B, A)) # merging channel lists into image
imageTK = ImageTk.PhotoImage(Image.fromarray(obj=image, mode='RGBA'))
canvasImage = canvas.create_image((0, 0), image=imageTK, anchor=NW)


def update(event=None):
    global scThreshVar, scCellWidthVar, scCellHeightVar, image

    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh_img = cv2.threshold(img, scThreshVar.get(), 255, cv2.THRESH_BINARY)

    canvas.delete('cell')

    stepX, stepY = scCellWidthVar.get(), scCellHeightVar.get()
    for x in range(0, CANVAS_WIDTH, stepX):
        for y in range(0, CANVAS_HEIGHT, stepY):
            cell = thresh_img[y:y + stepY, x:x + stepX]
            if len(cell[cell == 0]) / (stepX * stepY) > 0.5:
                canvas.create_rectangle([(x, y), (x + stepX, y + stepY)], outline='black', fill='black', tag='cell')


scThreshVar = IntVar()
scThreshVar.set(50)
scThresh = Scale(window, from_=0, to=255, variable=scThreshVar, orient=HORIZONTAL, length=150, command=update)
scThresh.place(x=820, y=150)

scCellWidthVar = IntVar()
scCellWidthVar.set(5)
scCellWidth = Scale(window, from_=2, to=20, variable=scCellWidthVar, orient=HORIZONTAL, length=150, command=update)
scCellWidth.place(x=820, y=300)

scCellHeightVar = IntVar()
scCellHeightVar.set(5)
scCellHeight = Scale(window, from_=2, to=20, variable=scCellHeightVar, orient=HORIZONTAL, length=150, command=update)
scCellHeight.place(x=820, y=380)

window.mainloop()

# def func():
#     top = Toplevel(root)
#     button_top_level = Button(top, text='Нажми', command=lambda: label.config(text='Текст из модального окна')).pack()
#     top.transient(root)
#     top.grab_set()
#     top.focus_set()
#     top.wait_window()
#
#
# root = Tk()
# label = Label(root, text='Текст')
# label.pack()
# button = Button(root, text='openModal', command=func).pack()
# root.mainloop()
