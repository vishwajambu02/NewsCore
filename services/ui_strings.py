UI_STRINGS = {
    'search_placeholder': {'en': 'Search news…', 'hi': 'समाचार खोजें…', 'gu': 'સમાચાર શોધો…', 'mr': 'बातम्या शोधा…', 'bn': 'সংবাদ খুঁজুন…', 'te': 'వార్తలు వెతకండి…', 'ta': 'செய்திகளைத் தேடுங்கள்…'},
    'go':              {'en': 'Go', 'hi': 'जाओ', 'gu': 'જાઓ', 'mr': 'जा', 'bn': 'যান', 'te': 'వెళ్ళు', 'ta': 'செல்'},
    'all':             {'en': 'All', 'hi': 'सभी', 'gu': 'બધા', 'mr': 'सर्व', 'bn': 'সব', 'te': 'అన్నీ', 'ta': 'அனைத்தும்'},
    'all_stories':     {'en': 'All Stories', 'hi': 'सभी समाचार', 'gu': 'બધા સમાચાર', 'mr': 'सर्व बातम्या', 'bn': 'সব খবর', 'te': 'అన్ని వార్తలు', 'ta': 'அனைத்து செய்திகள்'},
    'contact':         {'en': 'Contact', ...},
    'bookmarks':       {'en': 'Bookmarks', ...},
    'change_language': {'en': 'Change language', ...},
    'logout':          {'en': 'Logout', ...},
    'sign_in':         {'en': 'Sign In', ...},
    'about':           {'en': 'About', ...},
    'privacy':         {'en': 'Privacy', ...},
    'footer_copy':     {'en': '© 2026 NewsCore. AI-summarized news. Not financial or legal advice.', ...},
}

def t(key, lang):
    return UI_STRINGS.get(key, {}).get(lang) or UI_STRINGS.get(key, {}).get('en', key)
