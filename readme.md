# Anki Card Creator

This project automates the creation of vocabulary cards in Anki. It takes a simple list of translations, enriches them with grammatical information and example sentences using an AI model, generates text-to-speech audio for the foreign language words, and adds the final cards to your Anki collection.

## Quick Start

### 1. Install AnkiConnect

This tool requires the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on for Anki. Please install it by following the instructions on the add-on page (add-on ID: `2055492159`).

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/anki-creator.git
cd anki-creator
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up OpenAI API Key

Create a `.env` file in the root of the project and add your OpenAI API key:

```
OPENAI_API_KEY="your-key-here"
```

### 5. Configure the Language

Open `src/config.py` and set the `LANGUAGE` variable to the language you want to create cards for. The default is `"russian"`.

### 6. Create `vocab.txt`

Create a `vocab.txt` file in the root of the project. The format of this file depends on the selected language. See the `prompts/<language>/instructions.md` file for instructions on how to format the `vocab.txt` file for your chosen language.

### 7. Run the Script

Make sure Anki is running in the background, then run the script:

```bash
python src/main.py
```

The script will process your `vocab.txt` file and add the new cards to the Anki deck specified in `src/config.py`.

## How It Works

1.  **Parses Vocabulary:** The script reads the `vocab.txt` file, parsing each line into a translation pair.
2.  **Enriches Content:** For each pair, it calls the OpenAI API with a prompt from the `prompts/<language>` directory to get grammatical information and an example sentence.
3.  **Generates Audio:** It uses the OpenAI TTS API to generate audio for the foreign language text.
4.  **Creates Anki Cards:** It uses AnkiConnect to create new notes in Anki with the English word on the front, and the foreign word, grammatical information, example sentence, and audio on the back.

## Contributing

Contributions are welcome! Here are some ways you can help:

### Adding a New Language

1.  Create a new directory in the `prompts` directory with the name of the language (e.g., `prompts/french`).
2.  Inside the new directory, create two files:
    *   `prompt.txt`: This file should contain the prompt for the AI model to generate the card content. See the existing prompts for examples.
    *   `instructions.md`: This file should explain how to format the `vocab.txt` file for this language.
3.  Update the `src/config.py` file to set the `LANGUAGE` variable to your new language.
4.  Test your changes and open a pull request!

### Other Contributions

*   **Improve Prompts:** The prompts used to generate card content are in the `prompts` directory. You can improve the existing prompts or add new ones for different languages.
*   **Add Features:** Check out the roadmap below or propose your own ideas.
*   **Report Bugs:** If you find a bug, please open an issue.

## Roadmap

- [x] Create a prompt folder for prompts in different languages. Others can add prompts for languages or improve existing ones.
- [x] Make prompt chooseable by config
- [x] Add a readme quick start guide like remind to install anki extension
