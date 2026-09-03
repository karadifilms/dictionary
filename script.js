async function loadDictionary() {
    const dictionaryContainer = document.getElementById("dictionary");

    try {
        const response = await fetch("data.json");

        if (!response.ok) {
            throw new Error("Could not load data.json");
        }

        const words = await response.json();

        dictionaryContainer.innerHTML = "";

        const byDate = words.reduce((groups, word) => {
            (groups[word.date_added] = groups[word.date_added] || []).push(word);
            return groups;
        }, {});

        Object.entries(byDate).forEach(([date, group]) => {
            const groupElement = document.createElement("div");
            groupElement.className = "day-group";

            const dateHeader = document.createElement("div");
            dateHeader.className = "day-date";
            dateHeader.textContent = date;
            groupElement.appendChild(dateHeader);

            group.forEach(word => {
                const wordElement = document.createElement("div");
                wordElement.className = "word";

                wordElement.innerHTML = `
                    <div class="word-row">
                        <div class="kannada">${word.kannada}</div>
                        <div class="tulu">${word.tulu.join(", ")}</div>
                        <div class="english">${word.english}</div>
                    </div>
                `;

                groupElement.appendChild(wordElement);
            });

            dictionaryContainer.appendChild(groupElement);
        });

    } catch (error) {
        console.error(error);

        dictionaryContainer.innerHTML = `
            <p>Unable to load the dictionary.</p>
        `;
    }
}

loadDictionary();