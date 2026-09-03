async function loadDictionary() {
    const dictionaryContainer = document.getElementById("dictionary");

    try {
        const response = await fetch("data.json");

        if (!response.ok) {
            throw new Error("Could not load data.json");
        }

        const words = await response.json();

        dictionaryContainer.innerHTML = "";

        words.forEach(word => {
            const wordElement = document.createElement("div");
            wordElement.className = "word";

            wordElement.innerHTML = `
                <div class="word-row">
                    <div class="kannada">${word.kannada}</div>
                    <div class="tulu">${word.tulu}</div>
                    <div class="english">${word.english}</div>
                </div>

                <div class="date">
                    Added: ${word.date_added}
                </div>
            `;

            dictionaryContainer.appendChild(wordElement);
        });

    } catch (error) {
        console.error(error);

        dictionaryContainer.innerHTML = `
            <p>Unable to load the dictionary.</p>
        `;
    }
}

loadDictionary();