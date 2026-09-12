"""
services/ui_strings.py
Static UI-chrome translations (navbar, buttons, footer). This is
separate from article translation (services/translate_cache.py) —
this dict is fixed text, so it's just a lookup, no Gemini calls,
no cache needed.
"""

UI_STRINGS = {
    'search_placeholder': {
        'en': 'Search news…',
        'hi': 'समाचार खोजें…',
        'gu': 'સમાચાર શોધો…',
        'mr': 'बातम्या शोधा…',
        'bn': 'সংবাদ খুঁজুন…',
        'te': 'వార్తలు వెతకండి…',
        'ta': 'செய்திகளைத் தேடுங்கள்…',
    },
    'go': {
        'en': 'Go', 'hi': 'जाओ', 'gu': 'જાઓ', 'mr': 'जा',
        'bn': 'যান', 'te': 'వెళ్ళు', 'ta': 'செல்',
    },
    'all': {
        'en': 'All', 'hi': 'सभी', 'gu': 'બધા', 'mr': 'सर्व',
        'bn': 'সব', 'te': 'అన్నీ', 'ta': 'அனைத்தும்',
    },
    'all_stories': {
        'en': 'All Stories',
        'hi': 'सभी समाचार',
        'gu': 'બધા સમાચાર',
        'mr': 'सर्व बातम्या',
        'bn': 'সব খবর',
        'te': 'అన్ని వార్తలు',
        'ta': 'அனைத்து செய்திகள்',
    },
    'contact': {
        'en': 'Contact', 'hi': 'संपर्क करें', 'gu': 'સંપર્ક કરો',
        'mr': 'संपर्क', 'bn': 'যোগাযোগ', 'te': 'సంప్రదించండి', 'ta': 'தொடர்பு',
    },
    'bookmarks': {
        'en': 'Bookmarks', 'hi': 'बुकमार्क', 'gu': 'બુકમાર્ક',
        'mr': 'बुकमार्क', 'bn': 'বুকমার্ক', 'te': 'బుక్‌మార్క్‌లు', 'ta': 'புக்மார்க்குகள்',
    },
    'change_language': {
        'en': 'Change language',
        'hi': 'भाषा बदलें',
        'gu': 'ભાષા બદલો',
        'mr': 'भाषा बदला',
        'bn': 'ভাষা পরিবর্তন করুন',
        'te': 'భాష మార్చండి',
        'ta': 'மொழியை மாற்று',
    },
    'logout': {
        'en': 'Logout', 'hi': 'लॉग आउट', 'gu': 'લૉગ આઉટ',
        'mr': 'लॉग आउट', 'bn': 'লগ আউট', 'te': 'లాగ్ అవుట్', 'ta': 'வெளியேறு',
    },
    'sign_in': {
        'en': 'Sign In', 'hi': 'साइन इन करें', 'gu': 'સાઇન ઇન કરો',
        'mr': 'साइन इन करा', 'bn': 'সাইন ইন করুন', 'te': 'సైన్ ఇన్', 'ta': 'உள்நுழை',
    },
    'about': {
        'en': 'About', 'hi': 'हमारे बारे में', 'gu': 'અમારા વિશે',
        'mr': 'आमच्याबद्दल', 'bn': 'সম্পর্কে', 'te': 'గురించి', 'ta': 'எங்களை பற்றி',
    },
    'privacy': {
        'en': 'Privacy', 'hi': 'गोपनीयता', 'gu': 'ગોપનીયતા',
        'mr': 'गोपनीयता', 'bn': 'গোপনীয়তা', 'te': 'గోప్యత', 'ta': 'தனியுரிமை',
    },
    'footer_copy': {
        'en': '© 2026 NewsCore. AI-summarized news. Not financial or legal advice.',
        'hi': '© 2026 NewsCore. एआई-सारांशित समाचार। वित्तीय या कानूनी सलाह नहीं।',
        'gu': '© 2026 NewsCore. AI-સારાંશિત સમાચાર. નાણાકીય કે કાનૂની સલાહ નથી.',
        'mr': '© 2026 NewsCore. एआय-सारांशित बातम्या. आर्थिक किंवा कायदेशीर सल्ला नाही.',
        'bn': '© 2026 NewsCore. এআই-সারাংশিত সংবাদ। আর্থিক বা আইনি পরামর্শ নয়।',
        'te': '© 2026 NewsCore. AI-సారాంశ వార్తలు. ఆర్థిక లేదా న్యాయ సలహా కాదు.',
        'ta': '© 2026 NewsCore. AI-சுருக்கமான செய்திகள். நிதி அல்லது சட்ட ஆலோசனை அல்ல.',
    },
}


def t(key, lang):
    """Look up key in the current site language, falling back to
    English, then to the raw key if it's genuinely missing."""
    entry = UI_STRINGS.get(key, {})
    return entry.get(lang) or entry.get('en', key)
