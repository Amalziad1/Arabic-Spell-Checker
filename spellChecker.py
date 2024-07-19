from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.dediac import dediac_ar
from camel_tools.utils.normalize import normalize_unicode
from spellchecker import SpellChecker
import re
import string
import requests
from nltk.metrics.distance import edit_distance
from bs4 import BeautifulSoup


def fetch_corpus(url):
    # Send a GET request and retrieve the HTML content
    response = requests.get(url)
    html_content = response.content
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    # Find the content elements containing Arabic text
    content_elements = soup.find_all("p")
    # Extract Arabic text from the content elements
    arabic_corpus = []
    for element in content_elements:
        text = element.get_text()
        words = text.split()
        arabic_words = [word for word in words if word.isnumeric() or word.isalpha()]
        arabic_corpus.extend(arabic_words)
    return arabic_corpus

# Create a spell checker instance
spell_checker = SpellChecker(language='ar')

# Generate candidate corrections for a misspelled word
def generate_candidates(word):
    candidates = []
    # Get the most likely correct spelling for the word
    corrected_word = spell_checker.correction(word)
    # Generate spelling variations by adding, deleting, substituting, or transposing letters
    variations = spell_checker.candidates(word)
    if variations is not None:
        # Filter out the corrected word from the variations
        variations = [var for var in variations if var != corrected_word]
        candidates.extend(variations)
    return candidates,corrected_word

def preprocessCorpus(corpus):
    tokensss=[]
    for line in corpus:
        # remove numbers and punctuation
        line = re.sub(r'[0-9]+', '', line)
        line = line.translate(str.maketrans('', '', string.punctuation))
        # Remove diacritics
        text_without_diacritics = dediac_ar(line)
        # Normalize characters
        normalized_text = normalize_unicode(text_without_diacritics)
        # Tokenize the text
        tokens_ = simple_word_tokenize(normalized_text)
        tokensss.extend(tokens_)
    unique_tokens = set(tokensss)
    unique_tokens_list = list(unique_tokens)
    return unique_tokens_list




def rank_candidates(misspelled_word, candidates):
    distances = [(candidate, edit_distance(misspelled_word, candidate)) for candidate in candidates]
    ranked_candidates = sorted(distances, key=lambda x: x[1])[:5]
    return ranked_candidates

def prompt_user_for_correction(misspelled_word, expected_corrections):
    print(f"Misspelled Word: {misspelled_word}")
    print("Expected Corrections:")
    for i, correction in enumerate(expected_corrections):
        if(i==0):
            print(f"{i+1}. best suggested: {correction}")
        else:
            print(f"{i + 1}. {correction}")
    relatedChoices=[]
    while(1):
        related = input("Choose relevent corrections, click 0 to finish: ")
        while not related.isdigit() or int(related) < 0 or int(related) > len(expected_corrections):
            print("Invalid choice. Please enter a valid number.")
            related = input("Choose the desired correction (enter the corresponding number): ")
        if(int(related)==0):
            break
        if expected_corrections[int(related)-1] in relatedChoices:
            print("Already chosen")
        else:
            relatedChoices.extend(expected_corrections[int(related)-1])
    choice = input("Choose the desired correction (enter 0 if you want to delete this word): ")
    while not choice.isdigit() or int(choice) < 0 or int(choice) > len(expected_corrections):
        print("Invalid choice. Please enter a valid number.")
        choice = input("Choose the desired correction (enter the corresponding number): ")
    selected_correction = expected_corrections[int(choice)-1]
    index= int(choice)
    return selected_correction, index,relatedChoices

def calculate_accuracy(top_ranked_candidates, chosen_correction_index):
    total= len(top_ranked_candidates)
    selected=(total+1)-chosen_correction_index
    accuracy = selected / total if total > 0 else 0.0
    return accuracy
def calculate_precision(predicted_corrections, chosen_corrections):
    total_predictions = len(predicted_corrections)
    correct_predictions = len(chosen_corrections)
    precision = correct_predictions / total_predictions if total_predictions > 0 else 0.0
    return precision

#url = "https://ar.wikipedia.org/wiki/الصفحة_الرئيسية"
url = "https://ar.wikipedia.org/wiki/تأثير_اللغة_العربية_في_اللغة_الإسبانية"
arabic_corpus=fetch_corpus(url)
arabic_corpus=preprocessCorpus(arabic_corpus)
size= len(arabic_corpus)
print(arabic_corpus)
print(f"Size={size}")
correctedCorpus=[]
summedAcc=0
summedPrecision=0
count=0 #counting misspelled words
for word in arabic_corpus:
    candidates,corrected_word=generate_candidates(word)
    if len(candidates) != 0:
        top_candidates = rank_candidates(word, candidates)
        list = []
        list.append(corrected_word)
        top_candidates = list + top_candidates
        selected_word, index ,relatedChoices= prompt_user_for_correction(word, top_candidates)
        if index !=0:
            accuracy = calculate_accuracy(top_candidates, index)
            summedAcc += accuracy
            precision = calculate_precision(top_candidates, relatedChoices)
            summedPrecision += precision
            count += 1
            correctedCorpus.append(selected_word)
        # Else do nothing (no need to restore what the user wanted to delete
    else:
        correctedCorpus.append(word)
totalAcc=summedAcc/count if count>0 else 0
totalPre=summedPrecision/count if count>0 else 0
if count>0:
    print(f"Corrected Corpora: {correctedCorpus}")
    print(f"Accuracy={totalAcc}")
    print(f"Precision={totalPre}")
else:
    print("Your line is correct")
