from random import randint
from music21 import *
from tkinter import *
from tkinter import filedialog, ttk
import pygame, os, threading


def getChord(givenSeed):
    """
    a function to return a specific chord from a note
    Returns list which is the generated chord
    Parameter givenSeed: a list containing note id and chord type
    """
    ans = []
    if givenSeed[1] == 1:  # major triad
        ans = [givenSeed[0], givenSeed[0] + 4, givenSeed[0] + 7]
    if givenSeed[1] == 2:  # first inversion of major triad
        ans = [givenSeed[0] + 4, givenSeed[0] + 7, givenSeed[0] + 12]
    if givenSeed[1] == 3:  # second inversion of major triad
        ans = [givenSeed[0] + 7, givenSeed[0] + 12, givenSeed[0] + 16]
    elif givenSeed[1] == 4:  # minor triad
        ans = [givenSeed[0], givenSeed[0] + 3, givenSeed[0] + 7]
    elif givenSeed[1] == 5:  # first inversion of minor triad
        ans = [givenSeed[0] + 3, givenSeed[0] + 7, givenSeed[0] + 12]
    elif givenSeed[1] == 6:  # second inversion of minor triad
        ans = [givenSeed[0] + 7, givenSeed[0] + 12, givenSeed[0] + 15]
    elif givenSeed[1] == 7:  # diminished chord
        ans = [givenSeed[0], givenSeed[0] + 3, givenSeed[0] + 6]
    elif givenSeed[1] == 8:  # suspended second chords
        ans = [givenSeed[0], givenSeed[0] + 2, givenSeed[0] + 7]
    elif givenSeed[1] == 9:  # suspended fourth chord
        ans = [givenSeed[0], givenSeed[0] + 5, givenSeed[0] + 7]
    return ans


def getRandomNote():
    """
    function to generate a random chord
    Returns: a list of two integers (note ID, chord type)
    """
    return [randint(0, 120), randint(0, 9)]


class Gene:
    """
    A genome representing part of the music with offset 4.0

    Attribute chords: store the chords of this specific part
    Invariant: chords is a list

    """

    ### HIDDEN ATTRIBUTES
    # Attribute _score: store the score for this part
    # Invariant: _score is a double, or None if the algorithm has not started calculation score

    def __init__(self):
        """
        Consturctor initializes the chords list and score
        """
        self.chords = list()
        self._score = None

    def getScore(self):
        """
        Getter function to get the score of Genome
        Returns: private variable _score
        """
        return self._score

    def mutate(self):
        """
        mutaion function
        changes random position from the chords list to a random note
        """
        self.chords[randint(0, len(self.chords) - 1)] = getRandomNote()

    def generate(self):
        """
        function generates random chords of quarter size
        """
        self.chords.clear()
        for _ in range(4):
            self.chords.append(getRandomNote())

    def score(self, measures):
        """
        function to calculate the score of the measures
        Parameter measures: list of measures which represents the music stream from Population class
        """
        score = 0
        octaves = list()
        names = list()
        for measure in measures:
            for _chord in self.chords:
                _list = getChord(list(_chord))
                if len(_list) == 0:
                    score += 5
                for _note in _list:
                    octaveID = (_note) // 12
                    noteID = _note % 12
                    if octaveID in measure[1]:
                        score += 95
                    if noteID in measure[0]:
                        score += 45
                    octaves.append(octaveID)
                    names.append(noteID)

        self._score = score
        if len(set(names)) != 0:
            self._score = self._score / (
                2 * len(set(names))
            )  # divide by the number of different note names as a factor
        if len(set(octaves)) != 0:
            self._score = self._score / (
                2 * len(set(octaves))
            )  # divide by the number of different ocateves as a factor

    def crossOver(self, el1, el2):
        """
        crossover function for genome
        it takes the first half from the first genome and the second half from the second genome
        Prameter el1: first genome
        Prameter el2: second genome
        """
        self.chords.clear()
        for i in range(len(el1.chords)):
            if i < int(len(el1.chords) // 2):  # take the first half of the first genome
                self.chords.append(el1.chords[i])
            else:
                self.chords.append(el2.chords[i])

    def getAnalyses(self):
        """
        getAnalyses function analyses the measures from the chords list
        Returns: measure stream
        """
        ret = stream.Measure()
        array = []
        i = 0
        while i < len(self.chords):
            chordDuration = 1
            while (
                i + 1 < len(self.chords)
                and self.chords[i][0] == self.chords[i + 1][0]
                and self.chords[i][1] == self.chords[i + 1][1]
            ):
                chordDuration += 1
                i += 1
            array.append(
                (self.chords[i][0], self.chords[i][1], chordDuration)
            )  # here combine the same continuous chords
            i += 1

        for _chord in array:
            chordDuration = duration.Duration(_chord[2])
            if len(getChord(list(_chord))) != 0:
                ret.append(chord.Chord(getChord(list(_chord)), duration=chordDuration))
            else:
                ret.append(note.Rest(duration=chordDuration))
        return ret


class Population:
    """
    Population class to do the training, mutaions, and crossovers

    Attribute stream: represents the stream for input file
    Invariant: stream is a midi file stream

    Attribute genes: represents a list of genes for the algorithm
    Invarient: genes is a list of genes

    Attrivute results: represents the result generated from the algorithm
    Invariant: results is a list of genes which represents best output of the algorithm

    Attrivute numberOfParts: represents the number of parts in the input music file
    Invariant: numberOfParts is an integer represents the parts length
    """

    ### HIDDEN ATTRIBUTES
    # Attribute _measures: store the measures of the input file
    # Attribute _filename: store the input file name
    # Attribute _bestScore: store the best score evaluated from the algorithm
    stream = None
    _measures = None
    _bestScore = 0

    def __init__(self, filename):
        """
        contsructor for the Population
        Parameter filename: String contains midi file
        the constructer transfers the midi file to music21 stream
        """
        self.genes = []
        self.results = []

        midiFile = midi.MidiFile()
        midiFile.open(filename)
        midiFile.read()
        midiFile.close()
        self.stream = midi.translate.midiFileToStream(midiFile)
        self.analyze(self.stream.measureOffsetMap().items())
        self.numberOfParts = self.getLength()
        self.findKey()

    def mutate(self):
        """
        mutaion function does mutaions on the whole gene
        the probability of mutation the i-th position is 0.5
        this is done by checking is rnadint(0,1)==1 because it has a probability of 0.5
        """
        for _ in range(len(self.genes)):
            if randint(0, 1) == 1:
                self.genes[_].mutate()

    def findKey(self):
        """
        finding the key function uses music21 package's help to analyze the input stream
        It changes the music Key which is a label in tKinter, in order to show the key
        """
        key = self.stream.analyze("key")
        musicKey.set(key.tonic.name + " " + key.mode)
        self._filename = "output-" + key.tonic.name + key.mode[0] + ".mid"

    def generate(self):
        """
        generate function Generates random chords to fill the genes list
        """
        self.genes.clear()
        for _ in range(400):
            el = Gene()
            el.generate()
            self.genes.append(el)

    def getBest(self, index):
        """
        function getBest returns the best score from the genes and taking the best 20 genes
        """
        self.genes = self.genes[: len(self.genes)]
        for el in self.genes:
            el.score(
                self.getAnalayses()[index]
            )  # calculate the score for each one since the score might be None
        self.genes.sort(key=lambda _element: _element.getScore())
        self.genes = self.genes[::-1]
        self.genes = self.genes[:20]

    def crossOver(self):
        """
        crossover function to create new populations
        it does crossover for each pair of the first 20 genes
        """
        self.genes = self.genes[:20]
        for i in range(20):
            for j in range(20):
                if i == j:
                    continue
                el = Gene()
                el.crossOver(self.genes[i], self.genes[j])
                self.genes.append(el)
        self.mutate()

    def train(self):
        """
        train function iterates throught the strem parts and simulate the algorithm for the number of iteration specified by the user
        the final result for the funciton is saved by the function save
        also it stores the results from the function to self.results
        """
        self.results.clear()
        POPULATIONS = int(inputTxt.get())
        res = []
        score = 0
        fullProgress = self.numberOfParts
        currentProgress = 0
        for i in range(self.numberOfParts):
            self.generate()
            for j in range(POPULATIONS):
                self.getBest(i)
                if j + 1 < POPULATIONS:
                    self.crossOver()
            res.append(self.genes[0])
            score += self.genes[0].getScore()
            currentProgress = currentProgress + 1
            my_progress["value"] = float(currentProgress / fullProgress) * 100.0

        if score > self._bestScore:  # if the current score is higher just keep it
            self._bestScore = score
            self.results = res
            finalScore.set(score)
            p = stream.Part()
            for el in self.results:
                p.append(el.getAnalyses())
            self.save(p)

    @staticmethod
    def analyze(measure):
        """
        satic function to calculate the set with diffrent note's octave and names
        names are calculated by taking the measure modulo 12
        """
        arrayOctaves = []
        arrayNames = []
        for el1 in measure:
            if hasattr(el1, "isNote") and el1.isNote:
                arrayOctaves.append(el1.octave)
                arrayNames.append(el1.pitch.midi % 12)
            elif hasattr(el1, "isChord") and el1.isChord:
                for _note in el1.notes:
                    arrayOctaves.append(_note.poctave)
                    arrayNames.append(_note.pitch.midi % 12)
        return tuple([set(arrayNames), set(arrayOctaves)])

    def makeAnalyses(self, measures):
        self._measures = []
        for el in measures:
            array = []
            for measure in el[1]:
                array.append(self.analyze(measure))
            self._measures.append(array)

    def getAnalayses(self):
        """
        intitiate the stream parts by using measureOffsetMap function from music21 package
        """
        if self._measures is None:
            self.makeAnalyses(self.stream.measureOffsetMap().items())
        return self._measures

    def getLength(self):
        """
        dunction returns the length of stream parts
        """
        return len(self.stream.measureOffsetMap().items())

    def save(self, part):
        """
        function to to store the result of the algorithm
        parameter part: is the resuting output
        """
        s = self.stream
        s.insert(0, part)
        midiFile = midi.translate.streamToMidiFile(s)
        midiFile.open(self._filename, "wb")
        midiFile.write()
        midiFile.close()
        global midi_filename
        midi_filename = self._filename
        startButton["state"] = NORMAL  # enable the button


def openFile():
    """
    function to open the file
    it asks the user to choose midi file from his device
    """
    global population
    filePath = filedialog.askopenfilename(
        filetypes=[("midi files", "*.mid")]
    )  # force the user to choose midi file
    population = Population(
        filePath
    )  # initiate the Population to find the key used in the algorithm
    global generateAccompaniment
    generateAccompaniment["state"] = NORMAL  # enable the button


def startTraining():
    """
    starting function for the algorithm
    """
    my_progress["value"] = 0  # restart the progress bar
    population.train()


def play_music():
    """
    function to define the work of play the resulting music button
    it uses pygame to play the sound
    """
    if midi_filename is None:
        raise Exception("The file is not generated yet")
    freq = 44100  # audio CD quality
    bitsize = -16  # unsigned 16 bit
    channels = 2  # 1 is mono, 2 is stereo
    buffer = 1024  # number of samples
    pygame.mixer.init(freq, bitsize, channels, buffer)
    clock = pygame.time.Clock()
    pygame.mixer.music.load(midi_filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)  # check if playback has finished


def killProgram():
    """
    function to define the work of quit the program button
    """
    os._exit(0)


if __name__ == "__main__":
    """
    Entry point and defining the GUI structure
    """
    window = Tk()
    window.title("accompaniment generator")
    musicKey = StringVar()
    finalScore = StringVar()
    window.geometry("650x350")

    openFileButton = Button(
        text="Open MIDI file",
        command=lambda: threading.Thread(target=openFile).start(),
        width=25,
        height=2,
        bg="#69f5c6",
    )
    openFileButton.place(relx=0.35, rely=0.75, anchor=CENTER)

    global generateAccompaniment
    generateAccompaniment = Button(
        text="Generate accompaniment",
        command=lambda: threading.Thread(target=startTraining).start(),
        width=25,
        height=2,
        bg="#69f5c6",
        state=DISABLED,
    )
    generateAccompaniment.place(relx=0.65, rely=0.75, anchor=CENTER)

    global startButton
    startButton = Button(
        text="Play the resulting music",
        command=lambda: threading.Thread(target=play_music).start(),
        width=25,
        height=2,
        bg="#69f5c6",
        state=DISABLED,
    )
    startButton.place(relx=0.35, rely=0.9, anchor=CENTER)

    quitButtun = Button(
        text="Quit", command=killProgram, width=25, height=2, bg="#ff0f7f"
    )
    quitButtun.place(relx=0.65, rely=0.9, anchor=CENTER)

    label = Label(text="The key detected in the input file:")
    Output = Label(window, height=2, width=20, bg="light gray", textvariable=musicKey)
    label.place(relx=0.35, rely=0.1, anchor=CENTER)
    Output.place(relx=0.65, rely=0.1, anchor=CENTER)

    label = Label(text="The final score for the algorithm:")
    Output = Label(window, height=2, width=20, bg="light gray", textvariable=finalScore)
    label.place(relx=0.35, rely=0.3, anchor=CENTER)
    Output.place(relx=0.65, rely=0.3, anchor=CENTER)

    labelGeneration = Label(text="Number of generation to evaluate the music:")
    global inputTxt
    inputTxt = Entry(window, justify=CENTER)
    inputTxt.insert(0, 300)
    labelGeneration.place(relx=0.5, rely=0.5, anchor=CENTER)
    inputTxt.place(relx=0.5, rely=0.6, anchor=CENTER)

    my_progress = ttk.Progressbar(
        window, orient=HORIZONTAL, length=660, mode="determinate"
    )
    my_progress.place(relx=0.5, rely=1, anchor=CENTER)
    window.mainloop()
