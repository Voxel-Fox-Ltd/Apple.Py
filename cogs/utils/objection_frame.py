class ObjectionFrame(object):

    DEFENSE_CHARACTERS = {
        "Apollo Justice": 60,
        "Mia Fey": 15,
        "Miles Edgeworth (Defense)": 690,
        "Phoenix Wright": 1,
    }

    PROSECUTION_CHARACTERS = {
        "Franziska von Karma": 21,
        "Godot": 175,
        "Klavier Gavin": 65,
        "Manfred von Karma": 27,
        "Miles Edgeworth": 5,
        "Miles Edgeworth (Young)": 10,
        "Winston Payne": 19,
        "Winston Payne (Old)": 438,
        "Winston Payne (Young)": 564,
    }

    COUNSEL_CHARACTERS = {
        "Diego Armando": 45,
        "Ema Skye": 353,
        "Kristoph Gavin": 459,
        "Maggey Byrde": 370,
        "Marvin Grossberg": 360,
        "Maya Fey": 103,
        "Mia (as Maya)": 725,
        "Mia Fey": 121,
        "Phoenix Wright (Old)": 434,
        "Trucy Wright": 560,
    }

    JUDGE_CHARACTERS = {
        "Judge's Brother": 125,
        "Judge": 30,
        "Judge (AJ)": 606,
    }

    WITNESS_CHARACTERS = {
        "Acro": 322,
        "Adrian Andrews": 550,
        "Angel Starr": 419,
        "April May": 313,
        "BellBoy": 548,
        "Benjamin": 633,
        "Benjamin & Trilo": 634,
        "Bikini": 641,
        "Cody Hackins": 276,
        "Delila Hawthorne": 164,
        "Damon Gant": 92,
        "Daryan Crescend": 734,
        "Dee Vasquez": 426,
        "Desiree DeLite": 649,
        "Dick Gumshoe": 130,
        "Diego Armando": 653,
        "Director Hotti": 672,
        "Drew Misham": 655,
        "Elise Deuxnim": 678,
        "Ema Skye": 142,
        "Frank Sahwit": 71,
        "Franziska von Karma": 361,
        "Furio Tigre": 285,
        "Godot": 482,
        "Guy Eldoon": 659,
        "Ini Miney": 245,
        "Iris": 261,
        "Jake Marshall": 152,
        "Jean Armstrong": 489,
        "Klavier Gavin": 702,
        "Kristoph Gavin": 523,
        "Lana Skye": 194,
        "Larry Butz": 206,
        "Lisa Basil": 675,
        "Lotta Hart": 113,
        "Luke Atmey": 234,
        "Maggey Byrde": 386,
        "Manfred von Karma": 366,
        "Marvin Grossberg": 668,
        "Matt Engarde": 253,
        "Maxamillion Galactica": 579,
        "Maya Fey": 77,
        "Mia (as Maya)": 730,
        "Mia Fey": 541,
        "Mike Meekins": 391,
        "Miles Edgeworth": 220,
        "Moe": 572,
        "Morgan Fey": 554,
        "Pearl Fey": 469,
        "Penny Nichols": 630,
        "Phoenix Wright": 303,
        "Phoenix Wright (Old)": 461,
        "Redd White": 107,
        "Regina Berry": 294,
        "Richard Wellington": 371,
        "Ron DeLite": 331,
        "Sal Manella": 347,
        "Shelly de Killer": 617,
        "Shark Brushel": 708,
        "Terry Fawles": 620,
        "Trucy Wright": 589,
        "Vera Misham": 444,
        "Victor Kudo": 379,
        "Viola Cadaverini": 680,
        "Wendy Oldbag": 228,
        "Will Powers": 584,
        "Winfred Kitaki": 722,
        "Wocky Kitaki": 712,
        "Yanni Yogi": 338,
    }

    def __init__(self, text:str, character:str):
        self.text = text
        self.character = self.get_character_id(character)

    @classmethod
    def get_character_id(cls, name):
        for characters in [cls.DEFENSE_CHARACTERS, cls.PROSECUTION_CHARACTERS, cls.COUNSEL_CHARACTERS, cls.JUDGE_CHARACTERS, cls.WITNESS_CHARACTERS]:
            for i, o in characters.items():
                if name.lower() == i.lower():
                    return o
        raise KeyError()

    def to_json(self):
        return {
            "id": -1,
            "text": self.text,
            "poseId": self.character,
            "bubbleType": 0,
            "username":"",
            "mergeNext": False,
            "doNotTalk": False,
            "goNext": False,
            "poseAnimation": False,
            "flipped": False,
            "frameActions": [
            ],
            "frameFades": [
            ],
            "background": None,
            "characterId": None,
            "popupId": None
        }
