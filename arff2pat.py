######## Constants ########

ATTRIBUTE_HEADER_LABEL = "@attribute"
RELATION_HEADER_LABEL = "@relation"
DATA_LABEL = "@data"

REAL_ATTRIBUTE_DATATYPE = "real"
INTEGER_ATTRIBUTE_DATATYPE = "integer"
STRING_ATTRIBUTE_DATATYPE = "string"

ARFF_DICT_RELATION_KEY = "relation"
ARFF_DICT_ATTRIBUTES_KEY = "attributes"
ARFF_DICT_DATA_KEY = "data"

MISSING_DATUM = "?"

######## Some utility classes ########


# Exception indicating an error when reading an arff file
class ArffReadException(Exception):
    ERROR_STRING = "Error"
    AT_LINE = "at line"
    IN_FILE = "in file"

    def __init__(self, message=None, line=None, filename=None):
        self.message = message
        self.line = line
        self.filename = filename

    def __str__(self):
        returnedString = self.ERROR_STRING
        if self.message is not None:
            returnedString += ": " + self.message
        if self.line is not None:
            returnedString += " " + self.AT_LINE + " " + repr(self.line)
        if self.filename is not None:
            returnedString += " " + self.IN_FILE + " " + repr(self.filename)
        returnedString += "\n"
        return returnedString


# Class representing a simple attribute from an arff file
class Attribute:
    def __init__(self, name, isNumeric, possibleValues=[]):
        self.isNumeric = isNumeric
        self.name = name
        self.possibleValues = possibleValues

######## Main method ########


def main():
    import sys

    f = open(sys.argv[1])

    trainSplit = 50
    testSplit = 10
    validateSplit = 40

    arffData = dataFromArffFile(f)
    patData = arffDataToPatData(arffData[ARFF_DICT_ATTRIBUTES_KEY], arffData[ARFF_DICT_DATA_KEY])
    patDataToPatFile(sys.argv[2], arffData, patData, trainSplit, testSplit, validateSplit)

######## arff manipulation methods ########


# Parse an arff file, returning it in a usable format. This method returns a dictionary
# where:
#       key ARFF_DICT_RELATION_KEY returns the name of the relation
#       key ARFF_DICT_ATTRIBUTES_KEY returns a list of Attribute objects representing
#           the attributes of this relation
#       key ARFF_DICT_DATA_KEY returns a two-dimensional array of the data from the file
def dataFromArffFile(fileHandler):
    RELATION_READ_TWICE_MESSAGE = "@relation found twice"

    attributes = []
    data = []
    relation = ''
    foundRelation = False

    lineNumber = 0;

    for line in fileHandler:
        lineNumber += 1
        try:
            if line.lower().startswith(RELATION_HEADER_LABEL):
                if not foundRelation:
                    relation = readRelation(line)
                    foundRelation = True
                else:
                    raise ArffReadException(RELATION_READ_TWICE_MESSAGE)
            if line.lower().startswith(ATTRIBUTE_HEADER_LABEL):
                attributes.append(readAttribute(line))
            if line.lower().startswith(DATA_LABEL):
                data = readDataSection(fileHandler)
        except ArffReadException as e:
            e.line = lineNumber
            e.filename = fileHandler.name
            import sys

            sys.stderr.write(str(e))

    #TODO make these constant strings
    fileInfo = {ARFF_DICT_RELATION_KEY: relation, ARFF_DICT_ATTRIBUTES_KEY: attributes,
                ARFF_DICT_DATA_KEY: data}

    return fileInfo


# Parse the relation line in an arff header
def readRelation(relationLine):
    RELATION_LABEL_EXPECTED_MESSAGE = "@relation label expected but not found"

    if relationLine.lower().startswith(RELATION_HEADER_LABEL):
        return relationLine[len(RELATION_HEADER_LABEL):].strip().strip("\'")
    else:
        raise ArffReadException(RELATION_LABEL_EXPECTED_MESSAGE)


# Parse an attribute line in an arff header and return a corresponding Attribute object
def readAttribute(attributeLine):
    ATTRIBUTE_LABEL_EXPECTED_MESSAGE = "@attribute label expected but not found"

    if attributeLine.lower().startswith(ATTRIBUTE_HEADER_LABEL):
        name = getNameFromAttributeLine(attributeLine)
        isNumeric = getIsNumericFromAttributeLine(attributeLine)

        if not isNumeric:
            possibleValues = getPossibleValuesFromAttributeLine(attributeLine)
            return Attribute(name, isNumeric, possibleValues)
        else:
            return Attribute(name, isNumeric)

    else:
        raise ArffReadException(ATTRIBUTE_LABEL_EXPECTED_MESSAGE)


# Parse an attribute line in an arff header and return whether this attribute is numeric
def getIsNumericFromAttributeLine(attributeLine):
    return attributeLine.strip().endswith('real') or attributeLine.strip().endswith('integer')


# Parse an attribute line in an arff header and return the attribute's name
def getNameFromAttributeLine(attributeLine):
    #TODO do this with regex
    attributeName = attributeLine[len(ATTRIBUTE_HEADER_LABEL):]
    attributeName = attributeName.strip()
    if attributeName.startswith('\''):
        attributeName = attributeName[1:]
        attributeName = attributeName[:attributeName.find('\'')].strip('\'')
    else:
        attributeName = attributeName.split(" ", 1)[0]
    return attributeName


# Parse an attribute line in an arff header for a nominal attribute and return the set of
# its possible values
def getPossibleValuesFromAttributeLine(attributeLine):
    #TODO do this with regex
    csvAttributes = (attributeLine[attributeLine.find('{'):]).strip()
    csvAttributes = csvAttributes.lstrip('{').rstrip('}')
    csvAttributes = csvAttributes.replace(' ', '')
    return csvAttributes.split(',')


# Reads the data section of the arff file into a two-dimensional array
def readDataSection(fileHandler):
    data = []
    for line in fileHandler:
        data.append(readDataLine(line))
    return data


# Parses the comma separated values from a line in the data section of an arff file
def readDataLine(dataLine):
    thisLineData = dataLine.strip().split(',')

    for datum in thisLineData:
        datum = datum.strip()

    return thisLineData

######## pat manipulation methods ########


# Take the attributes and data from parsed arff data and return a two-dimensional array suitable
# for output into a pat file. This method will take nominal attributes and convert them to n-bit
# binary strings, where n is the number of possible values of the attribute. Missing values
# (indicated by a question mark) are simply ignored
def arffDataToPatData(attributes, data):
    BINARY_STRING_MAPPING_ERROR_MESSAGE = "Error when mapping nominal value to binary string"

    patData = []

    for dataLine in data:
        i = 0
        patDataLine = []
        badLineFlag = False
        for currentAttribute in attributes:

            if dataLine[i] == MISSING_DATUM:
                badLineFlag = True
                continue
            if currentAttribute.isNumeric:
                patDataLine.append(float(dataLine[i]))
            else:
                binaryString = [0] * len(currentAttribute.possibleValues)
                try:
                    binaryString[currentAttribute.possibleValues.index(dataLine[i])] = 1
                except Exception:
                    import sys

                    sys.stderr.write(BINARY_STRING_MAPPING_ERROR_MESSAGE)
                for bit in binaryString:
                    patDataLine.append(bit)

            i += 1

        if not badLineFlag:
            patData.append(list(patDataLine))

    return patData


# Take the two-dimensional array of pat data returned by arffDataToPatData, split into training,
# testing and validation sets, then write these to respective pat files.
def patDataToPatFile(baseFilename, arffData, patData, trainSplit, testSplit, validateSplit):
    TRAIN_PAT_FILE_SUFFIX = "_train.pat"
    TEST_PAT_FILE_SUFFIX = "_test.pat"
    VALIDATE_PAT_FILE_SUFFIX = "_validate.pat"

    # get the pat data
    pat = patData

    lastAttribute = arffData[ARFF_DICT_ATTRIBUTES_KEY][len(arffData[ARFF_DICT_ATTRIBUTES_KEY]) - 1]
    if lastAttribute.isNumeric:
        outputs = 1
    else:
        outputs = len(lastAttribute.possibleValues)

    inputs = len(pat[1]) - outputs

    # shuffle data
    import random

    random.shuffle(pat)

    # split into train, test and validate sets
    import math

    numTrain = int(math.floor((trainSplit / 100.0) * len(pat)))
    numTest = int(math.floor((testSplit / 100.0) * len(pat)))

    patTrain = pat[:numTrain]
    patTest = pat[numTrain:numTrain + numTest]
    patValidate = pat[numTrain + numTest:]

    trainFilename = baseFilename + TRAIN_PAT_FILE_SUFFIX
    testFilename = baseFilename + TEST_PAT_FILE_SUFFIX
    validateFilename = baseFilename + VALIDATE_PAT_FILE_SUFFIX
    uniqueFilenameNumber = 2

    import os.path

    # Generate unique filenames so as not to overwrite any existing outputs
    while (os.path.isfile(trainFilename)
           or os.path.isfile(testFilename)
           or os.path.isfile(validateFilename)):
        trainFilename = baseFilename + "_" + str(uniqueFilenameNumber) + TRAIN_PAT_FILE_SUFFIX
        testFilename = baseFilename + "_" + str(uniqueFilenameNumber) + TEST_PAT_FILE_SUFFIX
        validateFilename = baseFilename + "_" + str(uniqueFilenameNumber) + VALIDATE_PAT_FILE_SUFFIX

        uniqueFilenameNumber += 1

    # write data
    writePatFile(patTrain, trainFilename, inputs, outputs)
    writePatFile(patTest, testFilename, inputs, outputs)
    writePatFile(patValidate, validateFilename, inputs, outputs)


# Write a pat file containing the given data to the given filename
def writePatFile(data, filename, inputs, outputs):
    f = open(filename, 'w')
    f.write(patHeader(len(data), inputs, outputs))
    for dataLine in data:
        for datum in dataLine:
            f.write(str(datum))
            f.write(' ')
        f.write('\n')
    return


# Returns a pat file header constructed from the given parameters
def patHeader(numPatterns, numInputs, numOutputs):
    from datetime import datetime

    outputString = "SNNS pattern definition file V1.4\n"
    outputString += "generated at " + datetime.now().strftime("%a %b %d %H:%M:%S %Y\n")
    outputString += "\n"
    outputString += "No. of patterns : " + str(numPatterns) + "\n"
    outputString += "No. of input units : " + str(numInputs) + "\n"
    outputString += "No. of output units : " + str(numOutputs) + "\n"
    outputString += "\n"
    return outputString


if __name__ == '__main__': main()
