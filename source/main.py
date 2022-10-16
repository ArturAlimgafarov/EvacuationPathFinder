# 1. import libraries and modules
from config import *
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import asksaveasfile, askopenfile
from PIL import ImageTk, Image
import cv2
import numpy as np
import json
from a_star import astar

# 2. init main variables
# cells data structure: { key( (row_index, col_index) ): value( canvas_rect_id ) }
wallCells = {}
exitCells = {}
humanCells = {}

# flags
wallsHighlighted = False
gridDisplayed = False
wallsDisplayed = True
childIsOpen = False

# variables for selecting multiple cells
selectionRect = None
startX, startY = 0, 0
endX, endY = 0, 0
startCol, endCol = 0, 0
startRow, endRow = 0, 0
modelFilepath = None


# 3. init supporting functions
def refreshCells():
    global canvas, wallCells, humanCells, exitCells, wallsHighlighted, sbWidthVar, sbHeightVar

    cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()

    for pos in wallCells.keys():
        col, row = pos
        canvas.delete(wallCells[(col, row)])
        x, y = col * cellWidth, row * cellHeight
        fill = 'black' if wallsHighlighted and wallsDisplayed else ''
        outline = 'black' if wallsDisplayed else ''
        wallCells[(col, row)] = canvas.create_rectangle((x, y), (x + cellWidth, y + cellHeight),
                                                        outline=outline, fill=fill, tag='cell')

    for pos in exitCells.keys():
        col, row = pos
        tp = exitCells[pos][1]
        canvas.delete(exitCells[(col, row)][0])
        x, y = col * cellWidth, row * cellHeight
        exitCells[(col, row)] = (canvas.create_rectangle((x, y), (x + cellWidth, y + cellHeight),
                                                         outline='black', fill='lime', tag='cell'), tp)

    for pos in humanCells.keys():
        col, row = pos
        canvas.delete(humanCells[(col, row)])
        x, y = col * cellWidth, row * cellHeight
        humanCells[(col, row)] = canvas.create_rectangle((x, y), (x + cellWidth, y + cellHeight),
                                                         outline='black', fill='red', tag='cell')


def markingCell(col, row):
    global canvas, wallCells, exitCells, humanCells, sbWidthVar, sbHeightVar, rbVar

    cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()

    try:
        if rbVar.get() == 0:  # is wall
            canvas.delete(wallCells[(col, row)])
            del wallCells[(col, row)]
        elif rbVar.get() == 2:  # is exit
            canvas.delete(exitCells[(col, row)][0])
            del exitCells[(col, row)]
        elif rbVar.get() == 3:  # is human
            canvas.delete(humanCells[(col, row)])
            del humanCells[(col, row)]
    except KeyError:
        x, y = col * cellWidth, row * cellHeight
        if rbVar.get() == 0:  # is wall
            fill = 'black' if wallsHighlighted and wallsDisplayed else ''
            outline = 'black' if wallsDisplayed else ''
            wallCells[(col, row)] = canvas.create_rectangle((x, y), (x + cellWidth, y + cellHeight),
                                                            outline=outline, fill=fill, tag='cell')
        elif rbVar.get() == 2:  # is exit
            tpVar = []
            setThroughput(tpVar)
            tp = tpVar[0]
            if tp > 0:
                exitCells[(col, row)] = (canvas.create_rectangle((x, y), (x + cellWidth, y + cellHeight),
                                                                 outline='black', fill='lime', tag='cell'), tp)
        elif rbVar.get() == 3:  # is human
            humanCells[(col, row)] = canvas.create_rectangle((x, y), (x + cellWidth, y + cellHeight),
                                                             outline='black', fill='red', tag='cell')


def canvasRefresh():
    global arrayImage, panel, canvasImage, imagePosition
    imageTK = ImageTk.PhotoImage(Image.fromarray(obj=arrayImage, mode='RGBA'))  # convert numpy image to tkinter image
    canvas.delete(canvasImage)
    canvasImage = canvas.create_image(imagePosition, image=imageTK, anchor=NW)
    panel = Label(window, image=imageTK)
    panel.image = imageTK


def cellsFill():
    global wallsHighlighted
    wallsHighlighted = not wallsHighlighted
    refreshCells()


def displayGrid(isRefresh=None):
    global canvas, cursorCell, CANVAS_WIDTH, CANVAS_HEIGHT, gridDisplayed, sbWidthVar, sbHeightVar

    cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()

    if isRefresh:
        canvas.delete('grid_line')
        for i in range(0, CANVAS_WIDTH, cellWidth):
            canvas.create_line([(i, 0), (i, CANVAS_HEIGHT)], fill='gray', tag='grid_line')

        for i in range(0, CANVAS_HEIGHT, cellHeight):
            canvas.create_line([(0, i), (CANVAS_WIDTH, i)], fill='gray', tag='grid_line')
    else:
        if gridDisplayed:
            canvas.delete('grid_line')
            gridDisplayed = False
        else:
            for i in range(0, CANVAS_WIDTH, cellWidth):
                canvas.create_line([(i, 0), (i, CANVAS_HEIGHT)], fill='gray', tag='grid_line')

            for i in range(0, CANVAS_HEIGHT, cellHeight):
                canvas.create_line([(0, i), (CANVAS_WIDTH, i)], fill='gray', tag='grid_line')

            gridDisplayed = True

        canvas.delete((cursorCell))
        cursorCell = canvas.create_rectangle((0, 0), (cellWidth, cellWidth), outline='blue')
    refreshCells()


# 4. init basic UI event handlers
def mouseMove(event):
    global canvas, cursorCell, sbWidthVar, sbHeightVar

    cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()
    col, row = event.x // cellWidth, event.y // cellHeight
    x, y = col * cellWidth - 1, row * cellHeight - 1

    if rbVar.get() != 1:
        canvas.delete(cursorCell)
        cursorCell = canvas.create_rectangle((0, 0), (sbWidthVar.get(), sbHeightVar.get()), outline='blue')
        canvas.moveto(cursorCell, x, y)
    else:
        canvas.moveto(cursorCell, -cellWidth, -cellHeight)


def mousePress(event):
    global canvas, wallCells, wallsHighlighted, sbWidthVar, sbHeightVar, startX, startY, rbVar

    cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()
    startX, startY = event.x, event.y
    col, row = event.x // cellWidth, event.y // cellHeight

    canvas.delete('select_grid_line')
    if wallsDisplayed and rbVar.get() != 1:
        markingCell(col, row)


def mousePressMove(event):
    global canvas, selectionRect, startX, startY, endX, endY, sbWidthVar, sbHeightVar, imagePosition, arrayImage

    if rbVar.get() == 0:
        cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()
        endX, endY = event.x, event.y

        canvas.delete(selectionRect)
        selectionRect = canvas.create_rectangle((startX, startY), (endX, endY), outline='blue')

        try:
            col, row = startX // cellWidth, startY // cellHeight
            canvas.delete(wallCells[(col, row)])
            del wallCells[(col, row)]
        except KeyError:
            pass
    elif rbVar.get() == 1:
        h, w = arrayImage.shape[:2]
        imagePosition = event.x - w // 2, event.y - h // 2
        canvasRefresh()


def mouseUp(event):
    global canvas, CANVAS_WIDTH, CANVAS_HEIGHT, selectionRect, wallCells, startX, startY, endX, endY, \
        sbWidthVar, sbHeightVar, startCol, endCol, startRow, endRow

    if rbVar.get() == 0:
        cellWidth, cellHeight = sbWidthVar.get(), sbHeightVar.get()
        endX, endY = event.x, event.y

        canvas.delete(selectionRect)

        startCol = max(min(startX, endX), -cellWidth) // cellWidth + 1
        endCol = min(max(startX, endX), CANVAS_WIDTH) // cellWidth
        startRow = max(min(startY, endY), -cellHeight) // cellHeight + 1
        endRow = min(max(startY, endY), CANVAS_HEIGHT) // cellHeight

        if (endCol - startCol < 1) or (endRow - startRow < 1):
            return

        x1, x2 = startCol * cellWidth, endCol * cellWidth
        y1, y2 = startRow * cellHeight, endRow * cellHeight

        for i in range(x1, x2 + cellWidth, cellWidth):
            canvas.create_line([(i, y1), (i, y2)], fill='blue', tag='select_grid_line')

        for i in range(y1, y2 + cellHeight, cellHeight):
            canvas.create_line([(x1, i), (x2, i)], fill='blue', tag='select_grid_line')


def markingSelectionCells(event):
    global canvas, selectionRect, startRow, startCol, endRow, endCol

    if (endCol - startCol < 1) or (endRow - startRow < 1):
        return

    for row in range(startRow, endRow):
        for col in range(startCol, endCol):
            markingCell(col, row)

    startCol, endCol = 0, 0
    startRow, endRow = 0, 0


def resizeImage(event):
    global arrayImage, scaleValue, childIsOpen

    if childIsOpen:
        return

    scaleValue += event.delta // 120 * 0.01
    h, w = SOURCE_IMAGE.shape[:2]
    h, w = int(h * scaleValue), int(w * scaleValue)
    arrayImage = cv2.resize(SOURCE_IMAGE.copy(), (w, h))
    canvasRefresh()


def loadImage(event=None):
    global arrayImage, SOURCE_IMAGE, CANVAS_WIDTH, CANVAS_HEIGHT
    file = askopenfile(filetypes=(('PNG', '*png'), ('JPEG', '*jpeg *jpg'), ('All Files', '*.*')))
    image = np.asarray(Image.open(file.name))
    h, w = image.shape[:2]
    k = CANVAS_WIDTH / w if w > h else CANVAS_HEIGHT / h
    h, w = int(h * k), int(w * k)
    image = cv2.resize(image, (w, h))
    B, G, R = cv2.split(image)[:3]  # get color channels as lists
    alpha = 100  # transparency value
    A = np.ones(B.shape, dtype=B.dtype) * alpha  # image alpha-channel as list
    arrayImage = cv2.merge((R, G, B, A))  # merging channel lists into image
    SOURCE_IMAGE = arrayImage.copy()
    canvasRefresh()


def openFile(event=None):
    global imagePosition, arrayImage, scaleValue, SOURCE_IMAGE, canvasImage, wallCells, exitCells, humanCells, \
        sbWidthVar, sbHeightVar, modelFilepath

    if SOURCE_IMAGE is not None:
        ans = messagebox.askyesnocancel('Внимание', 'Сохранить открытый проект?')
        if ans is None:
            return
        else:
            if ans:
                save()
            else:
                pass

    file = askopenfile(filetypes=(('JSON Files', '*.json'), ('All Files', '*.*')))
    with open(file.name, 'r', encoding='utf-8') as j:
        data = json.loads(j.read())

    imageFilename = file.name.removesuffix('json') + 'png'
    SOURCE_IMAGE = np.asarray(Image.open(imageFilename, 'r'))
    if SOURCE_IMAGE is None:
        messagebox.showinfo('Ошибка', f'Изображение {imageFilename} не найдено')
        return

    canvas.delete(canvasImage)

    modelFilepath = file.name

    scaleValue = data['scale']
    imagePosition = data['image_position']['x'], data['image_position']['y']
    sbWidthVar.set(data['cell_size']['width'])
    sbHeightVar.set(data['cell_size']['height'])

    h, w = SOURCE_IMAGE.shape[:2]
    h, w = int(h * scaleValue), int(w * scaleValue)
    arrayImage = cv2.resize(SOURCE_IMAGE.copy(), (w, h))
    B, G, R = cv2.split(arrayImage)[:3]  # get color channels as lists
    alpha = 100  # transparency value
    A = np.ones(B.shape, dtype=B.dtype) * alpha  # image alpha-channel as list
    arrayImage = cv2.merge((R, G, B, A))  # merging channel lists into image
    SOURCE_IMAGE = arrayImage.copy()
    imageTK = ImageTk.PhotoImage(Image.fromarray(obj=arrayImage, mode='RGBA'))  # convert numpy image to tkinter image
    canvasImage = canvas.create_image(imagePosition, image=imageTK, anchor=NW)

    wallCells = {}
    exitCells = {}
    humanCells = {}
    canvas.delete('cell')

    for pos in data['walls']:
        col, row = pos['col'], pos['row']
        x, y = col * sbWidthVar.get(), row * sbHeightVar.get()
        fill = 'black' if wallsHighlighted and wallsDisplayed else ''
        outline = 'black' if wallsDisplayed else ''
        wallCells[(col, row)] = canvas.create_rectangle((x, y), (x + sbWidthVar.get(),
                                                                 y + sbHeightVar.get()),
                                                        outline=outline, fill=fill, tag='cell')
    for pos in data['exits']:
        col, row, tp = pos['col'], pos['row'], pos['throughput']
        x, y = col * sbWidthVar.get(), row * sbHeightVar.get()
        exitCells[(col, row)] = (canvas.create_rectangle((x, y), (x + sbWidthVar.get(),
                                                                  y + sbHeightVar.get()),
                                                         outline='black', fill='lime', tag='cell'), tp)

    canvasRefresh()
    refreshCells()


def save(event=None):
    global imagePosition, scaleValue, SOURCE_IMAGE, wallCells, exitCells, sbWidthVar, sbHeightVar

    data = {}
    data['image_position'] = {
        'x': imagePosition[0],
        'y': imagePosition[1]
    }
    data['scale'] = scaleValue
    data['cell_size'] = {
        'width': sbWidthVar.get(),
        'height': sbHeightVar.get()
    }

    data['walls'] = []
    for pos in wallCells.keys():
        col, row = pos
        data['walls'].append({
            'col': col,
            'row': row
        })
    data['exits'] = []
    for pos in exitCells.keys():
        col, row = pos
        tp = exitCells[pos][1]
        data['exits'].append({
            'col': col,
            'row': row,
            'throughput': tp
        })

    if SOURCE_IMAGE is None:
        messagebox.showinfo('Отмена', 'Сохранение невозможно. Отсутствует изображение проекта.')
        return

    if modelFilepath:
        with open(modelFilepath, 'w') as file:
            file.write(json.dumps(data, indent=4))
        imageFilename = file.name.removesuffix('json') + 'png'
        cv2.imwrite(imageFilename, SOURCE_IMAGE)
        messagebox.showinfo('Сохранение', f'Данные успешно сохранены в {modelFilepath}')
    else:
        file = asksaveasfile(initialfile='Untitled.json',
                             defaultextension='.json',
                             filetypes=(('All Files', '*.*'), ('JSON Files', '*.json')))

        imageFilename = file.name.removesuffix('json') + 'png'
        cv2.imwrite(imageFilename, SOURCE_IMAGE)
        file.write(json.dumps(data, indent=4))
        file.close()


def searchPaths():
    global canvas, wallCells, exitCells, humanCells, sbWidthVar, sbHeightVar
    cellSize = sbWidthVar.get(), sbHeightVar.get()

    exitTps = {pos: exitCells[pos][1] for pos in exitCells.keys()}
    if exitCells and humanCells:
        for human in humanCells.keys():
            variants = sorted([astar(wallCells, human, exit, cellSize) for exit in exitCells.keys()],
                              key=lambda item: item[2])
            path = []
            for v in variants:
                t, p, _ = v
                if exitTps[t] > 0:
                    path = p
                    exitTps[t] -= 1
                    break
                else:
                    continue

            # path = min([astar(wallCells, human, exit, cellSize) for exit in exitCells.keys()],
            #            key=lambda item: item[2])[1]

            for i in range(len(path) - 1):
                row1, col1 = path[i]
                row2, col2 = path[i + 1]
                x1, y1 = row1 * cellSize[0] + cellSize[0] // 2, col1 * cellSize[1] + cellSize[1] // 2
                x2, y2 = row2 * cellSize[0] + cellSize[0] // 2, col2 * cellSize[1] + cellSize[1] // 2
                canvas.create_line([(x1, y1), (x2, y2)], fill='darkgreen', width=2, tag='path')


def clearPaths():
    canvas.delete('path')
    canvasRefresh()


def openChildWindow():
    global window, rbVar, scaleValue, imagePosition, arrayImage, childIsOpen

    walls = set()
    childIsOpen = True

    rbVar.set(0)

    # set child window
    childWindow = Toplevel(window)
    childWindow.title('SEMI-AUTOMATIC BUILDING PLAN')
    childWindow.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
    childWindow.resizable(False, False)

    def update(a=None, b=None, c=None):
        global arrayImage, imagePosition

        if sbWidthVar2.get() < 2:
            sbWidthVar2.set(2)
        if sbWidthVar2.get() > 50:
            sbWidthVar2.set(50)

        if sbHeightVar2.get() < 2:
            sbHeightVar2.set(2)
        if sbHeightVar2.get() > 50:
            sbHeightVar2.set(50)

        offsetX, offsetY = abs(imagePosition[0]), abs(imagePosition[1])
        img = arrayImage[offsetY:offsetY + CANVAS_HEIGHT, offsetX:offsetX + CANVAS_WIDTH]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh_img = cv2.threshold(img, scThreshVar2.get(), 255, cv2.THRESH_BINARY)

        childCanvas.delete('cell')

        walls.clear()
        stepX, stepY = sbWidthVar2.get(), sbHeightVar2.get()
        for x in range(0, CANVAS_WIDTH, stepX):
            for y in range(0, CANVAS_HEIGHT, stepY):
                cell = thresh_img[y:y + stepY, x:x + stepX]
                if len(cell[cell == 0]) / (stepX * stepY) > 0.5:
                    childCanvas.create_rectangle([(x, y), (x + stepX, y + stepY)], outline='black', tag='cell')
                    col, row = x // stepX, y // stepY
                    walls.add((col, row))

    # add canvas to child window
    childCanvas = Canvas(childWindow, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
    childCanvas.place(x=CANVAS_OFFSET_X, y=CANVAS_OFFSET_Y)
    imageTK = ImageTk.PhotoImage(Image.fromarray(obj=arrayImage, mode='RGBA'))
    childCanvas.create_image(imagePosition, image=imageTK, anchor=NW)

    # add slider
    lbThresh2 = Label(childWindow, text='Пороговое значение')
    lbThresh2.place(x=818, y=230)
    scThreshVar2 = IntVar()
    scThreshVar2.set(50)
    scThresh2 = Scale(childWindow, from_=0, to=255, variable=scThreshVar2,
                      orient=HORIZONTAL, length=160, command=update)
    scThresh2.place(x=818, y=250)

    # add spinboxes
    lbSetCellWidth2 = Label(childWindow, text='Длина ячейки')
    lbSetCellWidth2.place(x=818, y=319)
    sbWidthVar2 = IntVar()
    sbWidthVar2.set(5)
    sbWidthVar2.trace('w', update)
    sbSetCellWidth2 = Spinbox(childWindow, from_=2, to=50, width=8, textvariable=sbWidthVar2, justify='center')
    sbSetCellWidth2.place(x=918, y=320)

    lbSetCellHeight2 = Label(childWindow, text='Высота ячейки')
    lbSetCellHeight2.place(x=818, y=349)
    sbHeightVar2 = IntVar()
    sbHeightVar2.set(5)
    sbHeightVar2.trace('w', update)
    sbSetCellHeight2 = Spinbox(childWindow, from_=2, to=50, width=8, textvariable=sbHeightVar2, justify='center')
    sbSetCellHeight2.place(x=918, y=350)

    # add buttons
    def apply():
        global sbWidthVar, sbHeightVar, wallCells

        sbWidthVar.set(sbWidthVar2.get())
        sbHeightVar.set(sbHeightVar2.get())

        wallCells = dict.fromkeys(walls, None)
        closingTop()
        refreshCells()

    def closingTop():
        global childIsOpen
        childIsOpen = False
        childWindow.destroy()

    btApply = Button(childWindow, text='Применить', command=lambda: apply(), width=20)
    btApply.place(x=830, y=511)

    btCancel = Button(childWindow, text='Отмена', command=lambda: closingTop(), width=20)
    btCancel.place(x=830, y=550)

    childWindow.protocol("WM_DELETE_WINDOW", closingTop)

    # first call
    update()

    childWindow.transient(window)
    childWindow.grab_set()
    childWindow.focus_set()
    childWindow.wait_window()


def setThroughput(tpVar: list):
    global window, childIsOpen

    childIsOpen = True

    # set child window
    childWindow = Toplevel(window)
    childWindow.title('INPUT THROUGHPUT')
    childWindow.geometry(f'300x150')
    childWindow.resizable(False, False)

    def update(a=None, b=None, c=None):
        if sbTPVar.get() < 1:
            sbTPVar.set(1)
        if sbTPVar.get() > 100:
            sbTPVar.set(100)

        if sbTPVar.get() < 1:
            sbTPVar.set(1)
        if sbTPVar.get() > 100:
            sbTPVar.set(100)

    # add spinbox
    lbSetTP = Label(childWindow, text='Введите пропускную способность:')
    lbSetTP.place(x=20, y=20)
    sbTPVar = IntVar()
    sbTPVar.set(1)
    sbTPVar.trace('w', update)
    sbSetTP = Spinbox(childWindow, from_=1, to=100, width=8, textvariable=sbTPVar, justify='center')
    sbSetTP.place(x=225, y=20)

    def apply():
        global childIsOpen
        tpVar.append(sbTPVar.get())
        childIsOpen = False
        childWindow.destroy()

    def closingTop():
        global childIsOpen
        tpVar.append(0)
        childIsOpen = False
        childWindow.destroy()

    btApply = Button(childWindow, text='Применить', command=lambda: apply(), width=20)
    btApply.place(x=80, y=65)

    btCancel = Button(childWindow, text='Отмена', command=lambda: closingTop(), width=20)
    btCancel.place(x=80, y=100)

    childWindow.protocol("WM_DELETE_WINDOW", closingTop)
    childWindow.transient(window)
    childWindow.grab_set()
    childWindow.focus_set()
    childWindow.wait_window()


# 5. init windows form elements and widgets
window = Tk()
window.title('BUILDING PLAN EDITOR')
window.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
window.resizable(False, False)

# add canvas
canvas = Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
canvas.place(x=CANVAS_OFFSET_X, y=CANVAS_OFFSET_Y)
canvasImage = None
arrayImage: np.array = None
SOURCE_IMAGE: np.array = None
imagePosition = (0, 0)
panel = None
scaleValue: float = 1.00

# add checkboxes
cbShowGridVar = BooleanVar()
cbShowGridVar.set(gridDisplayed)
cbShowGrid = Checkbutton(window, text='Отображать сетку', variable=cbShowGridVar, command=displayGrid)
cbShowGrid.place(x=818, y=12)

cbShowWallsVar = BooleanVar()
cbShowWallsVar.set(wallsDisplayed)


def cbShowWallsCommand():
    global wallsDisplayed
    wallsDisplayed = not wallsDisplayed
    refreshCells()


cbShowWalls = Checkbutton(window, text='Отображать препятствия', variable=cbShowWallsVar, command=cbShowWallsCommand)
cbShowWalls.place(x=818, y=35)

cbFillWallsVar = BooleanVar()
cbFillWallsVar.set(wallsHighlighted)
cbFillWalls = Checkbutton(window, text='Закрашивать препятствия', variable=cbFillWallsVar, command=cellsFill)
cbFillWalls.place(x=818, y=58)

# add radiobuttons
rbVar = IntVar()
rbVar.set(0)

rbSetWalls = Radiobutton(window, text='Установить препятствия', value=0, variable=rbVar)
rbSetWalls.place(x=818, y=130)

rbSetImagePos = Radiobutton(window, text='Установить положение\nплана', value=1, variable=rbVar)
rbSetImagePos.place(x=818, y=170)

rbSetExits = Radiobutton(window, text='Установить\nэвакуационные выходы', value=2, variable=rbVar)
rbSetExits.place(x=818, y=210)

rbSetHumans = Radiobutton(window, text='Установить положение\nлюдей', value=3, variable=rbVar)
rbSetHumans.place(x=818, y=250)


# add spinboxes
def refreshCellSize(a=None, b=None, c=None):
    global sbWidthVar, sbHeightVar, sbSetCellHeight, sbSetCellWidth

    if sbWidthVar.get() < 2:
        sbWidthVar.set(2)
    if sbWidthVar.get() > 50:
        sbWidthVar.set(50)

    if sbHeightVar.get() < 2:
        sbHeightVar.set(2)
    if sbHeightVar.get() > 50:
        sbHeightVar.set(50)

    if cbShowGridVar.get():
        displayGrid(True)
    refreshCells()


lbSetCellWidth = Label(window, text='Длина ячейки')
lbSetCellWidth.place(x=818, y=319)
sbWidthVar = IntVar()
sbWidthVar.set(5)
sbWidthVar.trace('w', refreshCellSize)
sbSetCellWidth = Spinbox(window, from_=2, to=50, width=8, textvariable=sbWidthVar, justify='center')
sbSetCellWidth.place(x=918, y=320)

lbSetCellHeight = Label(window, text='Высота ячейки')
lbSetCellHeight.place(x=818, y=349)
sbHeightVar = IntVar()
sbHeightVar.set(5)
sbHeightVar.trace('w', refreshCellSize)
sbSetCellHeight = Spinbox(window, from_=2, to=50, width=8, textvariable=sbHeightVar, justify='center')
sbSetCellHeight.place(x=918, y=350)

# add buttons
btOpenWindow = Button(window, text='Авто-конструктор', command=lambda: openChildWindow(), width=20)
btOpenWindow.place(x=830, y=394)

btTest = Button(window, text='Найти пути', command=lambda: searchPaths(), width=20)
btTest.place(x=830, y=433)

btClear = Button(window, text='Очистить пути', command=lambda: clearPaths(), width=20)
btClear.place(x=830, y=472)

btLoad = Button(window, text='Загрузить изображение', command=lambda: loadImage(), width=20)
btLoad.place(x=830, y=511)

btOpen = Button(window, text='Открыть', command=lambda: openFile(), width=20)
btOpen.place(x=830, y=550)

btSave = Button(window, text='Сохранить', command=lambda: save(), width=20)
btSave.place(x=830, y=589)

# graphic moving cursor cell
cursorCell = canvas.create_rectangle((0, 0), (sbWidthVar.get(), sbHeightVar.get()), outline='blue')

# 6. binding UI event handlers
# - keyboard events
window.bind('<space>', markingSelectionCells)
window.bind('<Control-s>', save)
window.bind('<Control-o>', openFile)

# - mouse events
canvas.bind('<MouseWheel>', resizeImage)
canvas.bind('<Button-1>', mousePress)
canvas.bind('<Motion>', mouseMove)
canvas.bind('<B1-Motion>', mousePressMove)
canvas.bind('<ButtonRelease-1>', mouseUp)

# 7. starting system/program
window.mainloop()
