import PySimpleGUI as sg
import openpyxl
import csv
import win32com.client as win32
import sys
import os
from pathlib import Path
import copy



###Nuts and Bolts Functions
def ConvertXLS(fname, curDir):
    fname2 = Path(curDir)/Path('Temp')/Path(fname) #converts to absolute path
    curDir2 = os.getcwd()
    fname = Path(curDir2)/Path(fname)
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    wb = excel.Workbooks.Open(fname)
    #check for temp folder, make if not there
    if not(os.path.isdir(Path(curDir)/Path('Temp'))):
        os.makedirs(Path(curDir)/Path('Temp'))
    #deletes old temp files if same name (should be cleaned after each run, but just in case)
    if os.path.isfile(str(fname2) + "x"):
        os.unlink(str(fname2) + "x")
    wb.SaveAs(str(fname2) + "x", FileFormat = 51)    #FileFormat = 51 is for .xlsx extension
    wb.Close()                               #FileFormat = 56 is for .xls extension
    excel.Application.Quit()

def ConvertsColsToCSV(colList):#converts from column letters to list index numbers for use with CSV files
    for i in range(len(colList)):
        colList[i] = openpyxl.utils.cell.column_index_from_string(colList[i]) - 1
        

def ColumnGrabber(outputSets, file1Sets, file2Sets, curdir):
    alpha = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ','BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ','CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV']
    file1Cols, f1check, tf1Cols = ColumnGrabberLoop(file1Sets)
    file2Cols, f2check, tf2Cols = ColumnGrabberLoop(file2Sets)
    
    if len(alpha) >= (len(file1Cols) + len(file2Cols) - 1): outCols = alpha[:(len(file1Cols) + len(file2Cols) - 1)] #gets the output columns based on how many columns there are total
    else:
        sg.Popup('There are too many output columns. \nPlease reduce to under 100 columns.')
        Quitter(curdir)
    return [outCols, file1Cols, file2Cols, f1check, f2check, tf1Cols, tf2Cols]


#used in ColumnGrabber()
def ColumnGrabberLoop(fileSets):
    #gets key position
    keyStarter = fileSets['Key']['Key']
    key = ''
    for i in keyStarter:
        if i.isdigit():
            key += i
    #creates a list of columns by letter
    colList = []
    fcheck = []
    tfCols = []
    for i in fileSets.keys():
        if i.startswith('Column '):
            if (fileSets[i]['Type'] == 'Exists'):
                if (fileSets[i]['Exists Definition'] == 'Skip Whole Line if False'):
                    fcheck += fileSets[i]['Column'],
                else:
                    tfCols += True,
                    colList += fileSets[i]['Column'],
            else:
                colList += fileSets[i]['Column'],
                tfCols += False,
    #these lines make sure the key column is always set to position 0 in the fcheck list and the colList
    key = colList[(int(key) - 1)]
    colList.remove(key) 
    colList.insert(0, key)
    fcheck.insert(0, key)
    #finish
    if fileSets['File Name'].endswith('csv'):
        ConvertsColsToCSV(colList)
        ConvertsColsToCSV(fcheck)
    return colList, fcheck, tfCols

def ObjGet(filename, filetype, curdir, folder):
    os.chdir(folder)
    if filetype == 'xlsx':
        if filename.endswith('xls'):
            try: filewb = openpyxl.load_workbook(filename + 'x')
            except Exception as error: FileDelErr('input', curdir, error)
        else:
            try: filewb = openpyxl.load_workbook(filename)
            except Exception as error: FileDelErr('input', curdir, error)
        fileobj = filewb.active
    elif filetype == 'csv':
        try: openfile = open(filename)
        except Exception as error: FileDelErr('input', curdir, error)
        fileobj = list(csv.reader(openfile, dialect='excel'))
    else:
        sg.Popup('The filetype of one of your inputs is bad. Closing.')
        sys.exit()
    os.chdir(curdir)
    return fileobj


#Loops through keys and saves any keys that will be printed (possible, settings-dependent exception if not in other file)
def KeyLooper(fileobj, filetype, needList):
    keyCol = needList[0]
    keysList = []
    if filetype == 'xlsx':
        row = StartRowXL(fileobj, keyCol)
        rowoffset = row
        nonecount = 0
        while nonecount < 5:
            value = str(fileobj[keyCol + str(row)].value)
            if value == 'None':
                nonecount += 1
            else:
                needKey = True
                for i in needList:
                    if not fileobj[i + str(row)].value:#if the column doesn't have a value
                        needKey = False #sets boolean for saving the key to false
                        break #optimizes
                if needKey:
                    keysList += value,
                else:
                    keysList.append(False) #allows index to remain intact
            row += 1
    elif filetype == 'csv':
        rowoffset = 0
        for row in fileobj:
            if row == 0:
                continue
            else:
                needKey = True
                for i in needList:
                    if not row[i]:#if the column doesn't have a value
                        needKey = False #sets boolean for saving the key to false
                        break #optimizes
                if needKey:
                    keysList += row[keyCol],
                else:
                    keysList.append(False) #allows index to remain intact
    return keysList, rowoffset


def StartRowXL(ws, col):
    startrow = 2
    skipper = 0
    headfound = False
    for i in range(1, 30):
        value = ws[col + str(i)].value
        if value == None:
            skipper += 1
        elif skipper < i:
            startrow = i
            break
    return startrow        


def FileTyper(fileSets, curDir):
    filetype = 'Bad'
    if fileSets['File Name'].endswith('xls'):
        #creates a .xlsx copy of the file
        ConvertXLS(fileSets['File Name'], curDir)
        filetype = 'xlsx'
        fileSets['File Folder'] = str(Path(curDir)/Path('Temp'))
    if fileSets['File Name'].endswith('xlsx'):
        filetype = 'xlsx'
    elif fileSets['File Name'].endswith('csv'):
        filetype = 'csv'
    return filetype


def RowGetter(obj, row, fileCols, filetype, tfCols):
    valueRow = []
    if filetype == 'xlsx':
        for c in range(len(fileCols)):
            if tfCols[c]:
                if obj[fileCols[c] + row].value:
                    valueRow += 'True',
                else:
                    valueRow += 'False',
            else:
                valueRow += obj[fileCols[c] + row].value,
    elif filetype == 'csv':
        for c in range(len(fileCols)):
            if tfCols[c]:
                if obj[int(row)][int(fileCols[c])]:
                    valueRow += 'True',
                else:
                    valueRow += 'False',
            else:
                try:
                    valueRow += obj[int(row)][int(fileCols[c])],
                except IndexError:
                    pass
                    #print('Index Error: ' + row)#debug
    return valueRow


def SheetCombinerStart(outputSets, file1Sets, file2Sets, curdir):
    #setup file paths and folders properly
    if (file1Sets['File Folder'] == '.\\') or (file1Sets['File Folder'] == './'):
        file1Sets['File Folder'] = curdir
    if (file2Sets['File Folder'] == '.\\') or (file2Sets['File Folder'] == './'):
        file2Sets['File Folder'] = curdir
    if (outputSets['Output Folder'] != '.\\') and (outputSets['Output Folder'] != './'): #relative path only used with default settings to indicate same folder as program
        os.chdir(outputSets['Output Folder'])
    #get output object to write to
    if outputSets['Output File Type'] == 'xlsx':
        outWB = openpyxl.Workbook()
        outObj = outWB.active
        outRow = 1
    elif outputSets['Output File Type'] == 'csv':
        try: outFile = open(outputSets['Output File Name'] + '.' + outputSets['Output File Type'], 'w', newline='')
        except Exception as error: FileDelErr('output', curdir, error)
        try: outObj = csv.writer(outFile, dialect='excel')
        except Exception as error: FileDelErr('output', curdir, error)
        outRow = 0#not strictly necessary
    #gets necessary columns for future checks
    outCols, file1Cols, file2Cols, f1check, f2check, tf1Cols, tf2Cols = ColumnGrabber(outputSets, file1Sets, file2Sets, curdir)
    
    filetype1 = FileTyper(file1Sets, curdir)
    filetype2 = FileTyper(file2Sets, curdir)
    
    file1 = ObjGet(file1Sets['File Name'], filetype1, curdir, file1Sets['File Folder'])
    file2 = ObjGet(file2Sets['File Name'], filetype2, curdir, file2Sets['File Folder'])
    keysList1, rowoff1 = KeyLooper(file1, filetype1, f1check)
    keysList2, rowoff2 = KeyLooper(file2, filetype2, f2check)
    
    #loading window setup
    loadernum = 1
    maxloadernum = 0
    maxloadernum += len(keysList1)
    if file2Sets['Key']['If One'] == 'Write Anyway':
        maxloadernum += len(keysList2)

    #prints column headers into output on first go-through
    needHeader = True
        
    #starts main transfer from file 1
    for index1, value in enumerate(keysList1):
        #skips writing if key value is a False placeholder
        if value == False:
            loadernum += 1#progress meter command
            sg.OneLineProgressMeter('Sheets Combining', loadernum, maxloadernum, 'key','The program is working.')
            continue
        
        if needHeader: #one-time special operations to make sure headings are properly transferred
            index2 = 0
            valueRow1 = RowGetter(file1, str(index1 + rowoff1), file1Cols, filetype1, tf1Cols)
            valueRow2 = RowGetter(file2, str(index2 + rowoff2), file2Cols, filetype2, tf2Cols)
            #overwrite True/False for headings that are Exists : Print True/False type
            for ind in range(len(tf1Cols)):
                if tf1Cols[ind]:
                    if filetype1 == 'xlsx':
                        valueRow1[ind] = file1[file1Cols[ind] + str(index1 + rowoff1)].value
                    elif filetype1 == 'csv':
                        valueRow1[ind] = file1[index1 + rowoff1][file1Cols[ind]]
            for ind in range(len(tf2Cols)):
                if tf2Cols[ind]:
                    if filetype2 == 'xlsx':
                        valueRow2[ind] = file2[file2Cols[ind] + str(index2 + rowoff2)].value
                    elif filetype2 == 'csv':
                        valueRow2[ind] = file2[index2 + rowoff2][file2Cols[ind]]
                        
            valueRow = valueRow1 + valueRow2[1:]
            if outputSets['Output File Type'] == 'xlsx':
                for i in range(len(valueRow)):
                    outObj[outCols[i] + str(outRow)] = valueRow[i]
                outRow += 1
            elif outputSets['Output File Type'] == 'csv':
                try: outObj.writerow(valueRow)
                except Exception as error: FileDelErr('output', curdir, error)
            needHeader = False
            
        #begin normal operations for data collection
        elif value in keysList2:
            index2 = keysList2.index(value)
            valueRow1 = RowGetter(file1, str(index1 + rowoff1), file1Cols, filetype1, tf1Cols)
            valueRow2 = RowGetter(file2, str(index2 + rowoff2), file2Cols, filetype2, tf2Cols)
            valueRow = valueRow1 + valueRow2[1:]
            if outputSets['Output File Type'] == 'xlsx':
                for i in range(len(valueRow)):
                    outObj[outCols[i] + str(outRow)] = valueRow[i]
                outRow += 1
            elif outputSets['Output File Type'] == 'csv':
                outObj.writerow(valueRow)
        elif file1Sets['Key']['If One'] == 'Write Anyway':
            valueRow = RowGetter(file1, str(index1 + rowoff1), file1Cols, filetype1, tf1Cols)
            for i in range(1, len(file2Cols)):
                if tf2Cols[i]:
                    valueRow.append('False')
                else:
                    valueRow.append('')
            if outputSets['Output File Type'] == 'csv':
                for i in range(len(file2Cols)):
                    if i == 0:
                        continue
                    else:
                        valueRow += None,
                try: outObj.writerow(valueRow)
                except Exception as error: FileDelErr('output', curdir, error)
            elif outputSets['Output File Type'] == 'xlsx':
                for i in range(len(valueRow)):
                    outObj[outCols[i] + str(outRow)] = valueRow[i]
                outRow += 1
        #progress meter commands
        loadernum += 1
        sg.OneLineProgressMeter('Sheets Combining', loadernum, maxloadernum, 'key','The program is working.')
        
    if file2Sets['Key']['If One'] == 'Write Anyway':
        for index2, value in enumerate(keysList2):

            #skips writing if key value is a False placeholder
            if value == False:
                loadernum += 1#progress meter commands
                sg.OneLineProgressMeter('Sheets Combining', loadernum, maxloadernum, 'key','The program is working.')
                continue
            
            if value not in keysList1:
                valueRow = RowGetter(file2, str(index2 + rowoff2), file2Cols, filetype2, tf2Cols)
                for i in range(1, len(file1Cols)):
                    if tf1Cols[i]:
                        valueRow.insert(i, 'False')
                    else:
                        valueRow.insert(i, '')
                if outputSets['Output File Type'] == 'csv':
                    #for i in range(len(file1Cols)):
                        #if i == 0:
                            #continue
                        #else:
                            #valueRow.insert(1, None)
                    try: outObj.writerow(valueRow)
                    except Exception as error: FileDelErr('output', curdir, error)
                elif outputSets['Output File Type'] == 'xlsx':
                    for i in range(len(valueRow)):
                        outObj[outCols[i] + str(outRow)] = valueRow[i]
                    outRow += 1
            #progress meter commands
            loadernum += 1
            sg.OneLineProgressMeter('Sheets Combining', loadernum, maxloadernum, 'key','The program is working.')
            
    #saves output as necessary and handles closing open output files
    if outputSets['Output File Type'] == 'csv':
        outFile.close()
        sg.Popup('All done and saved!')
    elif outputSets['Output File Type'] == 'xlsx':
        try:
            outWB.save(outputSets['Output File Name'] + '.' + outputSets['Output File Type'])
            sg.Popup('All done and saved!')
        except:
            try:
                outWB.save(outputSets['Output File Name'] + '-New' + '.' + outputSets['Output File Type'])
                sg.Popup('Could not save to specified name.\nSaved as ' + outputSets['Output File Name'] + '.' + outputSets['Output File Type'] + '-New')
            except: sg.Popup('Unable to save. Please check that all excel files are closed and try again.')
    Quitter(curdir)
    
#quits nicely
def Quitter(curdir):
    #clean out temp folder
    try:
        tempFiles = os.listdir(Path(curdir)/Path('Temp'))
        for file in tempFiles:
            os.unlink(Path(curdir)/Path('Temp')/Path(file))
    except FileNotFoundError:
        pass
    try: os.rmdir(Path(curdir)/Path('Temp'))
    except PermissionError:
        pass
    except FileNotFoundError:
        pass
    #ends program
    sys.exit()


#file deleted error
def FileDelErr(filetype, curdir, error):#takes a string ('csv' or 'xlsx'), then another string ('input' or 'output'), and then the starting directory for use with Quitter()
    sg.Popup('It appears that an ' + filetype + ' file has been moved or deleted.\nThe program will now quit.\n' + str(error) + '\nPlease try again, and be careful not to delete or move the files.')
    Quitter(curdir)


    

###GUI and Settings Functions
## dependency of GetSettings() that grabs inpur file data and nests properly
def FileSettings(keyname, fileSets, i, colname, colcount): ##filled by variables of same names in GetSettings setList loop
    if (keyname == 'File Name')|(keyname == 'File Folder'):
        fileSets[keyname] = i[:-1]
    elif (keyname == 'Column') | (keyname == 'Type') | (keyname == 'Exists Definition') | (keyname == 'Key') | (keyname == 'If One'):
        if keyname == 'Column':
            colname = keyname
            colname += ' '
            colname += str(colcount)
        elif keyname == 'Key':
            colname = keyname
        elif keyname == 'Exists Definition':
            colcount += 1
        try: fileSets[colname][keyname] = i[:-1]
        except: fileSets[colname] = {keyname : i[:-1]}
    return [fileSets, colname, colcount]

#gets the settings from the settings file
def GetSettings(setName):
    try:
        setFile = open(setName, 'r')
        setList = setFile.readlines()
        setFile.close()
        keyname = ' '
        counter = 0#uses modulo check to see if key or value, as well as increments past first (static) set of settings
        colcount = 1#allows settings to handle dynamic number of columns to be specified
        colname = 'Column X'#sets value in case somehow referenced before set
        section = 'Output'#handles if statements to determine which dict is being created
        outputSets = {}
        file1Sets = {}
        file2Sets = {}
        for i in setList:
            if (counter % 2) == 0:
                keyname = i[:-1]
                if keyname[1] == '#':
                    break
                counter += 1
                continue
            else:
                if section == 'Output':
                    outputSets[keyname] = i[:-1]
                    if counter >= 5:
                        section = 'File 1'
                elif section == 'File 1':
                    file1Sets, colname, colcount = FileSettings(keyname, file1Sets, i, colname, colcount)
                    if keyname == 'If One':
                        section = 'File 2'
                        colcount = 1
                elif section == 'File 2':
                    file2Sets, colname, colcount = FileSettings(keyname, file2Sets, i, colname, colcount)
                counter += 1
    except: #if the settings file cannot be found, this recreates default settings from scratch
        outputSets = {'Output File Name': 'Output', 'Output File Type': 'csv', 'Output Folder': '.\\'}
        file1Sets = {'File Name': '', 'File Folder':curdir, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
        file2Sets = {'File Name': '', 'File Folder':curdir, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
        SaveSettings(setName, outputSets, file1Sets, file2Sets)
    return [outputSets, file1Sets, file2Sets]

def TemplateWindow(file1Sets, file2Sets, curdir):
    checkWind = sg.Window('Demo Sheets', [[sg.Text('The default files were not found. \nWould you like to create some template sheets in the current directory for demo purposes, or would you like to specify the sheets to use by default?')],
                               [sg.Button('Template'), sg.Button('Select')],])
    while True:
        button, values = checkWind.Read()
        if button == 'Template':
            file1Sets = DefaultInputFile(file1Sets, '1', curdir)
            file2Sets = DefaultInputFile(file2Sets, '2', curdir)
        checkWind.close()
        if button == 'Select':
            select_layout = [
                [sg.Text('File 1 Name: '), sg.Input(file1Sets['File Folder'] + '\\' + file1Sets['File Name'], key='File 1 Name', enable_events=True), sg.FileBrowse(initial_folder=file1Sets['File Folder'], file_types=(('Excel Files', '*.xlsx'),('Ye Olde Excel Files', '*.xls'),('Comma Separated Values Files', '*.csv')))],
                [sg.Text('File 2 Name: '), sg.Input(file2Sets['File Folder'] + '\\' + file2Sets['File Name'], key='File 2 Name', enable_events=True), sg.FileBrowse(initial_folder=file2Sets['File Folder'], file_types=(('Excel Files', '*.xlsx'),('Ye Olde Excel Files', '*.xls'),('Comma Separated Values Files', '*.csv')))],
                [sg.Button('Done'), sg.Button('Cancel')],
                ]
            select_window = sg.Window('Select Default Files', select_layout)
            while True:
                button, values = select_window.Read()
                if button == 'Done':
                    FileNameFolder(values, 'File 1 Name', 'File 1 Folder')
                    file1Sets = {'File Name': values['File 1 Name'], 'File Folder':values['File 1 Folder'], 'Column 1': {'Column': 'A', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
                    FileNameFolder(values, 'File 2 Name', 'File 2 Folder')
                    file2Sets = {'File Name': values['File 2 Name'], 'File Folder':values['File 2 Folder'], 'Column 1': {'Column': 'A', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
                if button in (None, 'Done'):
                    select_window.close()
                    break
                if button == 'Cancel':
                    select_window.close()
                    TemplateWindow(file1Sets, file2Sets, curdir)
                    break
        break
    
    if not Path(file1Sets['File Folder']).exists():
            os.makedirs(Path(file1Sets['File Folder']))
    if not Path(file2Sets['File Folder']).exists():
            os.makedirs(Path(file2Sets['File Folder']))
    return file1Sets, file2Sets

#makes file in appropriate location
def DefaultInputFile(fileSets, filenum, curdir):
    filename = 'Template' + filenum + '.csv'
    if not (Path(curdir, filename).exists()):
        templateFile = open(filename, 'w', newline='')
        templateWriter = csv.writer(templateFile, dialect='excel')
        if filenum == '1':
            templateWriter.writerow(['Key', 'Date', 'Name'])
            templateWriter.writerow(['78544','1/5/2020', 'One'])
            templateWriter.writerow(['78546','1/6/2020', 'Two'])
            templateWriter.writerow(['78603','1/7/2020', 'Three'])
            templateWriter.writerow(['78659','1/9/2020', 'Four'])
            templateWriter.writerow(['78681','1/10/2020', 'Five'])
            templateWriter.writerow(['78715','1/11/2020', 'Six'])
            templateWriter.writerow(['78729','1/12/2020', 'Seven'])
            templateWriter.writerow(['78766','1/13/2020', 'Eight'])
            templateWriter.writerow(['78811','1/13/2020', 'Nine'])
            templateWriter.writerow(['78829','1/14/2020', 'Ten'])
            templateWriter.writerow(['78837','1/17/2020', 'Eleven'])
            templateWriter.writerow(['99999','1/1/2021', 'Fifty'])
        else:
            templateWriter.writerow(['Key', 'Description'])
            templateWriter.writerow(['78546','Red'])
            templateWriter.writerow(['78659','Orange'])
            templateWriter.writerow(['78700','Teal'])
            templateWriter.writerow(['78715','Yellow'])
            templateWriter.writerow(['78766','Green'])
            templateWriter.writerow(['78793','Puce'])
            templateWriter.writerow(['78811','Blue'])
            templateWriter.writerow(['78837','Purple'])
        templateFile.close()
    if filenum == '1':
        fileSets = {'File Name': filename, 'File Folder':curdir, 'Column 1': {'Column': 'A', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Column 2': {'Column': 'B', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Column 3': {'Column': 'C', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
    else:
        fileSets = {'File Name': filename, 'File Folder':curdir, 'Column 1': {'Column': 'A', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Column 2': {'Column': 'B', 'Type': 'Data', 'Exists Definition':'Skip Whole Line if False'}, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
    return fileSets #not strictly necessary

#checks that output folder exists, makes if necessary
def OutputSetsCleaner(outSets):
    if (outSets['Output Folder'] != '.\\') and (outSets['Output Folder'] != '\\') and (outSets['Output Folder'] != '/') and (outSets['Output Folder'] != './'):
        if not Path(outSets['Output Folder']).exists():
            os.makedirs(Path(outSets['Output Folder']))
    return outSets #not necessary

#checks that file name, file folder, and key column/column type are all valid for starting immediately
def SettingsCleaner(fileSets, filenum, curdir):
    unusedret, fileSets['File Folder'] = SlashCleaner(fileSets['File Folder'])
    if (fileSets['File Folder'] == '.\\') or (fileSets['File Folder'] == '\\') or (fileSets['File Folder'] == './') or (fileSets['File Folder'] == '/'):
        fileSets['File Folder'] = curdir
    #check for folder and check for file -- adjust filesets to template and then make template version if not present
    if (not Path(fileSets['File Folder']).exists()) or (not os.path.isfile(Path(fileSets['File Folder'], fileSets['File Name']))):
        fileSets = {'File Name': '', 'File Folder':curdir, 'Key': {'Key': 'Column 1', 'If One': 'Skip'}}
        return False
        if not Path(fileSets['File Folder']).exists():
            os.makedirs(Path(fileSets['File Folder']))
    #check that column key is set to is not Exists type-if it is, override column type and set to Data
    if not fileSets[fileSets['Key']['Key']]:
        fileSets[fileSets['Key']['Key']] = {'Column': 'Column 1', 'Type': 'Data', 'Exists Definition':'Skip Line'}
    if fileSets[fileSets['Key']['Key']]['Type'] == 'Exists':
        fileSets[fileSets['Key']['Key']]['Type'] = 'Data'
    return True

#gets headers from worksheets and returns dict by letter (csv has letter equivalent)
def HeadersByLetter(filename, filefolder, curdir, fileSets):
    alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ','BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ','CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV']
    headerDict = {}
    if (filefolder != '.\\') and (filefolder != '\\') and (filefolder != '/') and (filefolder != './'):
        os.chdir(filefolder)
    if filename.endswith('xls'):
        #creates temporary .xlsx file
        ConvertXLS(filename, curdir)
    if filename.endswith('csv'):
        try:#debug this should bring up an overridable error
            fileholder = open(filename, newline='')
            filereader = csv.reader(fileholder, dialect='excel')
            fileread = []
            index = 0
            try:#debug this should bring up an error
                for row in filereader:
                    index += 1
                    try: fileread.append(row)
                    except:
                        pass
            except:
                pass
            if len(fileread[0]) > len(alphabet):
                headerlen = len(alphabet)
            else:
                headerlen = len(fileread[0])
            for i in range(headerlen):
                headerDict[alphabet[i]] = fileread[0][i]
        except: return [headerDict, filename]
    elif (filename.endswith('xlsx')) or (filename.endswith('xls')):
        if filename.endswith('xlsx'):
            wb = openpyxl.load_workbook(filename)
        else:
            wb = openpyxl.load_workbook(str(Path(curdir)/Path('Temp')/Path(filename)) + 'x')
        ws = wb.active
        headerDict = {}
        rowcounter = 1
        foundBool = False
        while (rowcounter <= 3)&(not foundBool):
            colcounter = 0
            for j in alphabet:
                if colcounter >= 8:
                    break
                value = ws[j + str(rowcounter)].value
                if value != None:
                    foundBool = True
                    headerDict[j] = value
                else:
                    colcounter += 1
            rowcounter += 1
    if (filename.endswith('xls')):
        os.unlink(Path(curdir)/Path('Temp')/Path(filename + 'x'))#should delete temporary .xlsx file
    os.chdir(curdir)#changes cwd back to original
    HeaderClean(list(headerDict.keys()), fileSets)
    return [headerDict, filename]

#cleans the keys if header columns are not in the file
def HeaderClean(headerKeys, fileSets):
    lettercounter = 0
    for key in fileSets.keys():
        if key.startswith('Column '):
            if fileSets[key]['Column'] in headerKeys:
                lettercounter += 1
                if lettercounter >= len(headerKeys):
                    lettercounter = 0
            else:
                fileSets[key]['Column'] = headerKeys[lettercounter]
                lettercounter += 1
                if lettercounter >= len(headerKeys):
                    lettercounter = 0

#dependency of SaveSettings() that handles the appending
def SaveSettingsApp(setFile, key, value):
    if type(value) == type({}):
        for i in value.items():
            SaveSettingsApp(setFile, i[0], i[1])
    else:
        setFile.write((key + '\n'))
        setFile.write((value + '\n'))

#for saving new defaults to settings
def SaveSettings(setName, outputSets, file1Sets, file2Sets):
    setFile = open(setName, 'w')
    setFile.write('')
    setFile.close()
    setFile = open(setName, 'a')
    for i in outputSets.items():
        SaveSettingsApp(setFile, i[0], i[1])
    for i in file1Sets.items():
        if i[0] != 'Key':
            SaveSettingsApp(setFile, i[0], i[1])
    SaveSettingsApp(setFile, 'Key', file1Sets['Key'])
    for i in file2Sets.items():
        if i[0] != 'Key':
            SaveSettingsApp(setFile, i[0], i[1])
    SaveSettingsApp(setFile, 'Key', file2Sets['Key'])
    setFile.write('###')#sets this to allow a break check at the end of file (guards against accidental whitespace additions)
    setFile.close()

#adds a list of columns and checks that the dict is referring to real columns (will edit dict to real columns, so beware)
def ColumnReCalc(fileSets):
    alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ','BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ','CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV']
    fileCols, fileSets['File Name'] = HeadersByLetter(fileSets['File Name'], fileSets['File Folder'], curdir, fileSets)
    for key, value in fileSets.items():
        if not key.startswith('Column '):
            continue
        else:
            if value['Column'] not in fileCols.keys():
                try: value['Column'] = fileCols.keys()[alphabet.index(value['Column'])]
                except: value['Column'] = 'A'#fixes if it can't be assigned normally debug-bad handling, should specify the error
    return fileSets

#opens and controls main GUI window
def MainWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets):
    #sets up the layout for the main window
    mwLayout = [[sg.Text('File 1')],]
    for i in file1Sets.items():
        if not i[0].startswith('Column '):
            if i[0].startswith('File'):
                mwLayout += [sg.Text(i[0] + ': '), sg.Text(i[1])],
            continue
        else:
            mwLayout += [sg.Text(i[0] + ': '), sg.Text(i[1]['Column'], size=(16,1)), sg.Text('Type: '), sg.Text(i[1]['Type'])],
    mwLayout += [sg.Text('Key: ', size=(8,1)), sg.Text(file1Sets['Key']['Key'], size=(10,1)), sg.Text('If in Just One: '), sg.Text(file1Sets['Key']['If One'])],
    mwLayout += [sg.Text(' ', size=(20,1)), sg.Button('File 1 Settings')],
    mwLayout += [sg.Text('File 2')],
    for i in file2Sets.items():
        if not i[0].startswith('Column '):
            if i[0].startswith('File'):
                mwLayout += [sg.Text(i[0] + ': '), sg.Text(i[1])],
            continue
        else:
            mwLayout += [sg.Text(i[0] + ': '), sg.Text(i[1]['Column'], size=(16,1)), sg.Text('Type: '), sg.Text(i[1]['Type'])],
    mwLayout += [sg.Text('Key: ', size=(8,1)), sg.Text(file2Sets['Key']['Key'], size=(10,1)), sg.Text('If in Just One: '), sg.Text(file2Sets['Key']['If One'])],
    mwLayout += [sg.Text(' ', size=(20,1)), sg.Button('File 2 Settings')],
    mwLayout += [sg.Text('Output')],
    mwLayout += [sg.Text('Output File Name: '), sg.Text(outputSets['Output File Name']), sg.Text('.'), sg.Text(outputSets['Output File Type'])],
    mwLayout += [sg.Text('Output File Folder: '), sg.Text(outputSets['Output Folder'])],
    mwLayout += [sg.Text(' ', size=(20,1)), sg.Button('Output File Settings')],
    mwLayout += [sg.Button('Start'), sg.Button('Help'), sg.Button('Quit')],
    #sets up the actual window
    mainWind = sg.Window('Main Window', mwLayout)
    while True:
        button, values = mainWind.Read()
        if (button == 'File 1 Settings')|(button == 'File 2 Settings'):
            mainWind.close()
            FileSettingsWindow(outputSets, file1Sets, file2Sets, button, curdir, file1Resets, file2Resets)
        elif button == 'Output File Settings':
            mainWind.close()
            OutputWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
        elif (button == None) | (button == 'Quit'):
            mainWind.close()
            sys.exit()
        elif button == 'Help':
            mainWind.close()
            HelpWindow(outputSets, file1Sets, file2Sets, curdir, 0, file1Resets, file2Resets)
        elif button == 'Start':
            mainWind.close()
            SheetCombinerStart(outputSets, file1Sets, file2Sets, curdir)
            #add SheetCombinerStart function
        else:
            print('Error: Button not recognized.')
            mainWind.close()
            sys.exit()

#changes all slashes to proper joining, also returns last slash for splitting file and folder names from a path
def SlashCleaner(thestring):
    lastslash = 0
    newpath = Path('/')
    stringList = thestring.split('/')
    if len(stringList) < 2:#if no split occurred on the prev line
        stringList = thestring.split('\\')
    if len(stringList) > 1:
        for i in stringList:
            if ':' in i:
                newpath = newpath / (Path(i + '\\'))
            else: newpath = newpath / (Path(i))
    newstring = str(newpath)
    lastslash = len(newstring) - len(stringList[-1]) - 1
    return lastslash, newstring

#check key is set to column with type data

def SlashReplacer(thestring):
    newstring = ''
    for i in thestring:
        if i != '\\':
            newstring += i
        else:
            newstring += '/'
    return newstring


def FileNameFolder(values, key, key2):
    splitter, values[key] = SlashCleaner(values[key])
    values[key2] = values[key][:splitter + 1]
    values[key] = values[key][(splitter + 1):]


#updates the file settings dict passed from a settings window
def UpdateFileDict(values, fileSets, colHeads):
    #split filepath into foldername and filename
    FileNameFolder(values, 'File Name', 'File Folder')
    
    #make lists of keys so dicts may be modified during iteration
    setKeys = list(fileSets)
    valKeys = list(values)
    
    colExVals = {}
    headinc = 0
    headList = list(colHeads.keys())
    for key in setKeys:
        if key.startswith('Column '):
            if fileSets[key]['Column'] != '':
                colExVals[key] = {'Type':fileSets[key]['Type'], 'Exists Definition':fileSets[key]['Exists Definition']}
            del fileSets[key]#so that autonumbering can be used--yes, it should have been a list of columns instead
    for key in valKeys:
        if type(key) != type('abc'):#checks that the key is a string and skips if it isn't
            continue
        elif key.startswith('Column '):
            if key in values:
                for alpha, heading in colHeads.items():#converts headings back into alpha for use with main
                    if values[key] == heading:
                        values[key] = alpha
                if values[key] == '':#cleans up values from returned extra columns
                    del values[key]
                    try: del values[(key + ' Type')]
                    except: pass
                    try: del values[(key + ' Exists Definition')]
                    except: pass
                    continue
                if key in colExVals:
                    values[key] = {'Column':values[key]}
                    values[key]['Type'] = colExVals[key]['Type']
                    values[key]['Exists Definition'] = colExVals[key]['Exists Definition']
                else:
                    values[key] = {'Column':values.get(key, headList[headinc])}
                    values[key]['Type'] = 'Data'
                    values[key]['Exists Definition'] = 'Skip Whole Line if False'
                    headinc += 1
            tempkey = key
            if len(key) > 8:
                tempkey = tempkey[:9]
                if not tempkey[8].isdigit():
                    tempkey = tempkey[:8]
                if tempkey in values:
                    if values[tempkey] != '':
                        fileSets[tempkey] = values[key]
            else:
                if tempkey not in fileSets:
                    fileSets[tempkey] = {}
                fileSets[tempkey] = values[key]
        elif key == 'Browse':
            del values[key]
        else:
            if (key == 'Key')|(key == 'If One'):
                for k in fileSets['Key']:
                    if values[k] == '':
                        if key == 'Key':
                            fileSets['Key'][k] = 'Column 1'
                        else:
                            fileSets['Key'][k] = 'Write Anyway'
                    else:
                        fileSets['Key'][k] = values[k]
            else:
                fileSets[key] = values[key]
    #makes sure that columns start counting from 1
    colnums = []#create matched blank lists
    colvals = []
    for key in fileSets:
        if key.startswith('Column '):
            if len(key) == 8: #determines if one or two digit number
                num = key[-1:]
            else:
                num = key[-2:]
            #add number and value to matched lists (to preserve order)
            colnums += num,
            colvals += fileSets[key],
    #overwrites previous column data, deletes if necessary
    for i in range(len(colnums)):#number of entries that need to be modified, based on prev. loop
        del fileSets['Column ' + colnums[i]]
        fileSets['Column ' + str(i + 1)] = colvals[i]
    return fileSets

#opens and controls either the File 1 Settings window or the File 2 Settings window
def FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets): #(dict, dict, dict, str, str, dict, dict)
    print(file1Sets)#debug
    
    if windName.startswith('File 1'):
        fileSets = file1Sets
    elif windName.startswith('File 2'):
        fileSets = file2Sets
    else:
        sg.Popup('You got here via the wrong button somehow! \nExiting now.')
        sys.exit()
    
    fileCols, fileSets['File Name'] = HeadersByLetter(fileSets['File Name'], fileSets['File Folder'], curdir, fileSets)
    
    headList = ['']
    for i in fileCols:
        headList += fileCols[i],
    if fileSets['File Folder'] == '.\\':
        fileSets['File Folder'] = curdir
    
    repeatcheckfilename = fileSets['File Folder'] + '\\' + fileSets['File Name']
    repeatcheckfilename = SlashReplacer(repeatcheckfilename)
    
    endColNum = 1
    swLayout = [
        [sg.Text('File Name: '), sg.Input(fileSets['File Folder'] + '\\' + fileSets['File Name'], key='File Name', enable_events=True), sg.FileBrowse(initial_folder=fileSets['File Folder'], file_types=(('Excel Files', '*.xlsx'),('Ye Olde Excel Files', '*.xls'),('Comma Separated Values Files', '*.csv')))],
        ]
    for i in fileSets.items():
        if not i[0].startswith('Column '):
            continue
        else:
            print(i)#debug
            swLayout += [sg.Text(i[0] + ': '), sg.Combo(headList, default_value=fileCols[i[1]['Column']], size=(16,1), key=i[0], enable_events=True), sg.Text('Type: '), sg.Text(i[1]['Type'])],
            endColNum = int(i[0][7:]) + 1
    swLayout += [sg.Text('Column ' + str(endColNum) + ': '), sg.Combo(headList, size=(16,1), key='Column ' + str(endColNum), enable_events=True), sg.Text('Type: '), sg.Text('Data'),],
    swLayout += [sg.Text(''),],
    swLayout += [sg.Text('Key'),],
    keycols = []
    for i in range(1, endColNum):
        if fileSets['Column ' + str(i)]:
            if (fileSets['Column ' + str(i)].get('Type', 'Blank')) == 'Exists':
                continue
        keycols += ('Column ' + str(i)),
    swLayout += [sg.Text('Key Column: '), sg.Combo(keycols, size=(16,1), key='Key', default_value=fileSets['Key']['Key']),],
    swLayout += [sg.Text('If Just in One: '), sg.Combo(['Skip', 'Write Anyway'], default_value=fileSets['Key']['If One'], size=(16,1), key='If One')],
    swLayout += [sg.Text(''),],
    swLayout += [sg.Button('Recalculate Columns'), sg.Button('Advanced Settings')],
    swLayout += [sg.Button('Okay'), sg.Button('Set as Defaults'), sg.Button('Restore Values'), sg.Cancel()],
    setWind = sg.Window(windName, swLayout)
    while True:
        button, values = setWind.Read()
        if button == 'Cancel':
            setWind.close()
            MainWindow(outputSets, copy.deepcopy(file1Resets), copy.deepcopy(file2Resets), curdir, file1Resets, file2Resets)
        elif (button == None):
            MainWindow(outputSets, copy.deepcopy(file1Resets), copy.deepcopy(file2Resets), curdir, file1Resets, file2Resets)
        elif (button == 'File Name'):
            if values['File Name'] != repeatcheckfilename:
                repeatcheckfilename = [values['File Name'],]
                repeatcheckfilename = SlashReplacer(repeatcheckfilename)
                fileSets = UpdateFileDict(values, fileSets, fileCols)
                setWind.close()
                FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets)
        elif (button == 'Recalculate Columns'):
            fileSets = UpdateFileDict(values, fileSets, fileCols)
            setWind.close()
            FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets)
        elif (button.startswith('Column ')):
            if (values[button] == '') or (button == 'Column ' + str(endColNum)):
                fileSets = UpdateFileDict(values, fileSets, fileCols)
                setWind.close()
                FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets)
        elif button == 'Okay':
            if fileSets[values['Key']]['Type'] == 'Exists':
                sg.Popup('Please set the Key to a column with Type: Data.')
            else:
                fileSets = UpdateFileDict(values, fileSets, fileCols)
                setWind.close()
                MainWindow(outputSets, file1Sets, file2Sets, curdir, copy.deepcopy(file1Sets), copy.deepcopy(file2Sets))
        elif button == 'Set as Defaults':
            if fileSets[values['Key']]['Type'] == 'Exists':
                sg.Popup('Please set the Key to a column with Type: Data.')
            else:
                warnLayout = [[sg.Text('Warning: This action cannot be undone.')],
                              [sg.Text('Continue?')],
                              [sg.Button('Yes'), sg.Button('No')],]
                warnWind = sg.Window('Warning: Set as Defaults').Layout(warnLayout)
                wbutton, wvalues = warnWind.read()
                if wbutton == 'Yes':
                    warnWind.close()
                    fileSets = UpdateFileDict(values, fileSets, fileCols)
                    setWind.close()
                    SaveSettings(setName, outputSets, file1Sets, file2Sets)
                    FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, copy.deepcopy(file1Sets), copy.deepcopy(file2Sets))
                else: warnWind.close()
        elif button == 'Restore Values':
            setWind.close()
            FileSettingsWindow(outputSets, copy.deepcopy(file1Resets), copy.deepcopy(file2Resets), windName, curdir, file1Resets, file2Resets)
        elif button == 'Advanced Settings':
            setWind.close()
            AdvancedTypesWindow(outputSets, file1Sets, file2Sets, windName, curdir, fileSets, fileCols, file1Resets, file2Resets)
        else:
            sg.Popup('Congratulations. You pushed a button that shouldn\'t exist.')
            

#updates the advanced settings only
def UpdateAdvancedDict(values, fileSets, fileCols):
    for key in values:
        key1 = key[:9]
        if not key1[8].isdigit():
            key1 = key1[:8]
            key2 = key[9:]
        else:
            key2 = key[10:]
        if key1 not in fileSets:
            fileSets[key1] = {'Column':fileCols.keys()[0]}
        fileSets[key1][key2] = values[key]
    return fileSets #not strictly necessary

#makes sure at least one column is a Data type so it can be used as a key, sets bool to let window generate popup
def AdvancedValueCatcher(values):
    isvalid = False
    for key, value in values.items():
        if key.startswith('Column '):
            if key.endswith('Type'):
                if value == 'Data':#one data value makes the whole thing valid
                    isvalid = True
                    break #no need to check the rest
    return isvalid

def AdvancedTypesWindow(outputSets, file1Sets, file2Sets, windName, curdir, fileSets, fileCols, file1Resets, file2Resets):
    atLayout = []
    for i in fileSets.items():
        if not i[0].startswith('Column '):
            continue
        else:
            atLayout += [sg.Text(i[0] + ': '), sg.Text(fileCols[i[1]['Column']], size=(16,1)), sg.Text('Type: '), sg.Combo(['Data','Exists'], default_value=i[1]['Type'], key=(i[0] + ' Type'))],
            atLayout += [sg.Text('How to handle the Exists Type: '), sg.Combo(['Skip Whole Line if False', 'Print True/False'], default_value=i[1]['Exists Definition'], key=(i[0] + ' Exists Definition'))],
            atLayout += [sg.Text('')],
    atLayout += [sg.Button('Okay'), sg.Button('Set as Defaults'), sg.Button('Restore Values'), sg.Cancel()],

    atWind = sg.Window((windName + ' Advanced Settings'), atLayout)
    while True:#GUI loop
        button, values = atWind.read()
        if button == 'Cancel':
            atWind.close()
            FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets)
        elif (button == None):
            FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets)
        elif button == 'Okay':
            if AdvancedValueCatcher(values):#checks if there is a valid column for use with the key
                fileSets = UpdateAdvancedDict(values, fileSets, fileCols)
                atWind.close()
                FileSettingsWindow(outputSets, file1Sets, file2Sets, windName, curdir, file1Resets, file2Resets)
            else:
                sg.Popup('Please set at least one column to the Data type so it may be used as a key.')
        elif button == 'Set as Defaults':
            if AdvancedValueCatcher(values):#checks if there is a valid column for use with the key
                warnLayout = [[sg.Text('Warning: This action cannot be undone.')],
                              [sg.Text('Continue?')],
                              [sg.Button('Yes'), sg.Button('No')],]
                warnWind = sg.Window('Warning: Set as Defaults').Layout(warnLayout)
                wbutton, wvalues = warnWind.read()
                if wbutton == 'Yes':
                    warnWind.close()
                    fileSets = UpdateAdvancedDict(values, fileSets, fileCols)
                    atWind.close()
                    SaveSettings(setName, outputSets, file1Sets, file2Sets)
                    AdvancedTypesWindow(outputSets, file1Sets, file2Sets, windName, curdir, fileSets, fileCols, file1Resets, file2Resets)
                else: warnWind.close()
            else:
                sg.Popup('Please set at least one column to the Data type so it may be used as a key.')
        elif button == 'Restore Values':
            atWind.close()
            AdvancedTypesWindow(outputSets, file1Sets, file2Sets, windName, curdir, fileSets, fileCols, file1Resets, file2Resets)
        else:
            sg.Popup('Congratulations. You pushed a button that shouldn\'t exist.')
                       

def OutputWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets):
    if outputSets['Output Folder'] == '.\\':
        outputSets['Output Folder'] = curdir
    owLayout = [[sg.Text('Output File Name'), sg.InputText(outputSets['Output File Name'], key='Output File Name', justification='right', size=(43,1)), sg.Text('.'), sg.Combo(['csv', 'xlsx'], default_value=outputSets['Output File Type'], key='Output File Type'),],
                [sg.Text('Output File Folder'), sg.InputText(outputSets['Output Folder'], size=(40,1), key='Output Folder'), sg.FolderBrowse(initial_folder=outputSets['Output Folder']),],
                [sg.Button('Okay'), sg.Button('Set as Defaults'), sg.Button('Restore Defaults'), sg.Cancel()],
                ]
    outWind = sg.Window('Output Settings', owLayout)
    while True:
        button, values = outWind.read()
        if button == 'Cancel':
            outWind.close()
            MainWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
        elif (button == None):
            MainWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
        elif button == 'Okay':
            somenum, values['Output Folder'] = SlashCleaner(values['Output Folder'])
            for key in outputSets:
                outputSets[key] = values[key]
            outWind.close()
            MainWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
        elif button == 'Set as Defaults':
            warnLayout = [[sg.Text('Warning: This action cannot be undone.')],
                          [sg.Text('Continue?')],
                          [sg.Button('Yes'), sg.Button('No')],]
            warnWind = sg.Window('Warning: Set as Defaults').Layout(warnLayout)
            wbutton, wvalues = warnWind.read()
            if wbutton == 'Yes':
                somenum, values['Output Folder'] = SlashCleaner(values['Output Folder'])
                for key in outputSets:
                    outputSets[key] = values[key]
                SaveSettings('Settings.txt', outputSets, file1Sets, file2Sets)
            warnWind.close()
        elif button == 'Restore Defaults':
            outWind.close()
            OutputWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
        else:
            sg.Popup('Congratulations. You pushed a button that shouldn\'t exist.')

def HelpWindow(outputSets, file1Sets, file2Sets, curdir, dispNum, file1Resets, file2Resets):
    colText = '''The program will present you with the column headings it 
finds in a drop-down menu. Columns headings can only be 
detected up to column 100 (CV). The program cannot
distinguish column headings from the first line of data
in a sheet with no headings, so be sure all files used
have headings added.

Columns will always appear in the output spreadsheet in 
the order they have in the File Settings menus. (The key 
column is an exception to this.) First is the Key column. 
Then the rest of the File 1 columns, in order. Then the 
File 2 columns in order (also without the key).

TYPE
This field has two values: Data or Exists.

Data simply puts the same value in the output sheet as is 
in the input sheet for that row and column.

Exists allows a column to output a True/False value 
instead of its nominal value when it is put into the 
Output sheet. Having any value in the field is True, and 
having no value at all is False.'''
    filText = '''This program supports .csv and .xlsx files. It has 
partial support for .xls files as inputs only. 

.XLSX FILES
This program always uses the active sheet. Please be 
careful when using excel workbooks with multiple sheets 
that the active sheet (the one that pops up when the file 
is initially opened) is the sheet you would like to 
parse.

.XLS FILES
Files with the type .xls are only partially supported; 
they will be converted to .xlsx files and stored in the
Temp folder while the program is run. The converted file
will be deleted when no longer in use.

The conversion process is a little slow when navigating
the settings menu, but does not substantially slow the
program when run.

.CSV FILES
CSV files are the fastest type of file to use in this
program. When parsing files with more than a thousand
lines, it may be worth converting the input files to
.csv format and selecting .csv for the output type.
'''
    keyText = '''The key column is the column that lets the program know 
what data to use to match the two spreadsheet rows. 
Please choose a unique value to avoid issues with 
incorrect or unpredictable matching. This column will
always appear in the output spreadsheet. Keys should
not be assigned to any column that has the 'Exists'
type, only 'Data' columns. (See Advanced Settings
help for more details.)

The key column will always appear in the far left of the 
output spreadsheet. It will have the same heading as the
File 1 Input sheet does for the column. The heading does
not need to match the File 2 heading for its key column.

IF JUST IN ONE
This value lets the program know if you want a row 
included even if it is only in one of the two 
spreadsheets. For example, when linking product inventory 
to description, you might want a SKU to appear if it has 
a description, even if it is out of stock and therefore 
not in the product inventory sheet.

Choose Skip if you do not want the values to appear. 
Choose Write Anyway if you want the key to appear even if 
only some of the values will be in the output 
spreadsheet.

Please note that this is set separately for each input 
sheet. Be sure to change them both if you want them to 
match!'''
    advText = '''Advanced settings allow you to control the behavior of
the output file more closely. You can set whether the
output file will contain the actual row value ('Data')
or if you simply need to know that there was a value at
all in the input file ('Exists').

If you have selected the 'Exists' input type, then you
can choose whether the data will be printed in the output
sheet as 'True' (if present) or 'False' (if not present),
or if the entire row will be printed at all (if present)
or skipped (if not present).

Be very careful with these settings, as they can interact
in hard to predict ways, especially if multiple columns
are set to 'Exists' AND 'Skip Whole Line if False'. If
you don't want to deal with this type of interaction,
input type 'Data' is always safe and predictable.

Please note that using 'Cancel' or 'Reset Values' in the
main Settings window will also cancel changes made in the
Advanced Settings window.

SKIP WHOLE LINE IF FALSE
In the same sheet, false overpowers true. If multiple
columns are set to 'Exists' and have this setting,
any one column not having data in the cell will disable
the entire row from being printed.

But what if the other sheet has an entry for that key?
This actually depends on a 'Key' setting in the main
settings window for the other sheet. Skipped rows will
mimic the 'If Just in One' behavior. They will not print
for that sheet, but they will print from the other sheet
if the key exists there and 'If Just in One' is set to
'Write Anyway' for that sheet.
'''
    
    textList = [colText, filText, keyText, advText]
    headingList = ['Columns', 'Files', 'Key Columns', 'Advanced Settings']
    buttonList = []
    for i in range(len(headingList)):
        if i == dispNum:
            buttonList += [sg.Button(headingList[i], button_color=('white', 'dark green'))],
        else:
            buttonList += [sg.Button(headingList[i], button_color=('white', 'dark blue'))],
    
    helpLay = [
        [sg.Column(buttonList), sg.Column([[sg.Text(headingList[dispNum]),],[sg.Text(textList[dispNum])],], scrollable=True),],
        [sg.Button('Main Menu'),],
        ]
    helpWind = sg.Window('Help', helpLay)
    while True:
        button, values = helpWind.read()
        if button == None:
            sys.exit()
        elif button == 'Main Menu':
            helpWind.close()
            MainWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
        else:
            helpWind.close()
            HelpWindow(outputSets, file1Sets, file2Sets, curdir, headingList.index(button), file1Resets, file2Resets)


###Main program
curdir = os.getcwd()
setName = '.\\Settings.txt'
outputSets, file1Sets, file2Sets = GetSettings(setName)
file1Check = SettingsCleaner(file1Sets, '1', curdir)#(settings dict, numeral indicating which file, current working dir)
file2Check = SettingsCleaner(file2Sets, '2', curdir)#(settings dict, numeral indicating which file, current working dir)
if (not file1Check) or (not file2Check):
    file1Sets, file2Sets = TemplateWindow(file1Sets, file2Sets, curdir)
SaveSettings(setName, outputSets, file1Sets, file2Sets)
outputSets = OutputSetsCleaner(outputSets)
file1Sets = ColumnReCalc(file1Sets)
file2Sets = ColumnReCalc(file2Sets)
file1Resets = copy.deepcopy(file1Sets)
file2Resets = copy.deepcopy(file2Sets)
MainWindow(outputSets, file1Sets, file2Sets, curdir, file1Resets, file2Resets)
Quitter(curdir)#should never be run, but just in case
