async function loadDictionary() {
    const dictionaryContainer = document.getElementById("dictionary");

    try {
        const response = await fetch("data.json", {cache: 'no-store'});

        if (!response.ok) {
            throw new Error("Could not load data.json");
        }

        const words = await response.json();

        dictionaryContainer.innerHTML = "";

        const byDate = words.reduce((groups, word) => {
            (groups[word.date_added] = groups[word.date_added] || []).push(word);
            return groups;
        }, {});

        function formatDate(dateStr) {
            const [year, month, day] = dateStr.split("-").map(Number);
            return new Date(year, month - 1, day).toLocaleDateString("en-US", {
                year: "numeric", month: "long", day: "numeric"
            });
        }

        const sortedEntries = Object.entries(byDate).sort(([a], [b]) => b.localeCompare(a));

        sortedEntries.forEach(([date, group]) => {
            const groupElement = document.createElement("div");
            groupElement.className = "day-group";

            const dateHeader = document.createElement("div");
            dateHeader.className = "day-date";
            dateHeader.textContent = formatDate(date);
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