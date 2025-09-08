import random


class WordGenerator:
    def __init__(self):
        # 常用辅音字母
        self.consonants = "bcdfghjklmnpqrstvwxyz"
        # 元音字母
        self.vowels = "aeiou"
        # 常用的字母组合
        self.common_pairs = [
            "th",
            "ch",
            "sh",
            "ph",
            "wh",
            "br",
            "cr",
            "dr",
            "fr",
            "gr",
            "pr",
            "tr",
        ]
        # 常用的词尾
        self.common_endings = ["ing", "ed", "er", "est", "ly", "tion", "ment"]
        # 常用的用户名后缀
        self.username_suffixes = [
            "123",
            "888",
            "666",
            "777",
            "999",
            "pro",
            "cool",
            "good",
            "best",
        ]

    def generate_syllable(self):
        """生成一个音节"""
        if random.random() < 0.3 and self.common_pairs:  # 30% 概率使用常用字母组合
            return random.choice(self.common_pairs) + random.choice(self.vowels)
        else:
            return random.choice(self.consonants) + random.choice(self.vowels)

    def generate_word(self, min_length=4, max_length=8):
        """生成一个随机单词"""
        word = ""
        target_length = random.randint(min_length, max_length)

        # 添加音节直到达到目标长度附近
        while len(word) < target_length - 2:
            word += self.generate_syllable()

        # 可能添加常用词尾
        if random.random() < 0.3 and len(word) < max_length - 2:
            word += random.choice(self.common_endings)
        elif len(word) < target_length:
            word += random.choice(self.consonants)

        return word.lower()

    def generate_random_username(self, min_length=3, max_length=8):
        """生成随机用户名"""
        username = self.generate_word(min_length, max_length)

        # 50% 的概率添加数字或特殊后缀
        if random.random() < 0.5:
            if random.random() < 0.7:  # 70% 概率添加数字
                username += str(random.randint(0, 999)).zfill(random.randint(2, 3))
            else:  # 30% 概率添加特殊后缀
                username += random.choice(self.username_suffixes)

        return username

    def generate_combined_username(self, num_words=1, separator="_"):
        """生成完整的组合用户名"""
        # 首先生成基础用户名
        base_username = self.generate_random_username()

        # 生成额外的随机单词
        words = [self.generate_word() for _ in range(num_words)]

        # 随机决定用户名放在前面还是后面
        if random.random() < 0.5:
            words.append(base_username)
        else:
            words.insert(0, base_username)

        return separator.join(words)