let selectedFile = null;

const imageInput = document.getElementById("imageInput");
const dropZone = document.getElementById("dropZone");

const filePreview = document.getElementById("filePreview");
const previewImage = document.getElementById("previewImage");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const removeImage = document.getElementById("removeImage");

const analyzeButton = document.getElementById("analyzeButton");
const buttonText = document.getElementById("buttonText");
const loader = document.getElementById("loader");

const errorMessage = document.getElementById("errorMessage");

const emptyResults = document.getElementById("emptyResults");
const resultContent = document.getElementById("resultContent");
const resultTitle = document.getElementById("resultTitle");
const resultStatus = document.getElementById("resultStatus");

const caloriesValue = document.getElementById("caloriesValue");
const proteinValue = document.getElementById("proteinValue");
const carbsValue = document.getElementById("carbsValue");
const fatValue = document.getElementById("fatValue");

const ingredientsBody = document.getElementById("ingredientsBody");
const warningsBox = document.getElementById("warnings");


/* --------------------------------
   FILE SELECTION
-------------------------------- */

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    if (file) {
        handleFile(file);
    }
});


function handleFile(file) {

    hideError();

    const allowedTypes = [
        "image/jpeg",
        "image/png"
    ];

    if (!allowedTypes.includes(file.type)) {
        showError("Please select a JPEG or PNG image.");
        resetFile();
        return;
    }

    selectedFile = file;

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    previewImage.src = URL.createObjectURL(file);

    filePreview.classList.remove("hidden");

    analyzeButton.disabled = false;
}


function formatFileSize(bytes) {

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}


/* --------------------------------
   DRAG & DROP
-------------------------------- */

["dragenter", "dragover"].forEach(eventName => {

    dropZone.addEventListener(eventName, event => {

        event.preventDefault();

        dropZone.classList.add("dragging");
    });

});


["dragleave", "drop"].forEach(eventName => {

    dropZone.addEventListener(eventName, event => {

        event.preventDefault();

        dropZone.classList.remove("dragging");
    });

});


dropZone.addEventListener("drop", event => {

    const file = event.dataTransfer.files[0];

    if (file) {
        handleFile(file);
    }

});


/* --------------------------------
   REMOVE IMAGE
-------------------------------- */

removeImage.addEventListener("click", () => {

    resetFile();

});


function resetFile() {

    selectedFile = null;

    imageInput.value = "";

    if (previewImage.src) {
        URL.revokeObjectURL(previewImage.src);
    }

    previewImage.src = "";

    filePreview.classList.add("hidden");

    analyzeButton.disabled = true;

    hideError();
}


/* --------------------------------
   ANALYZE
-------------------------------- */

analyzeButton.addEventListener("click", async () => {

    if (!selectedFile) {
        showError("Please select a meal image first.");
        return;
    }

    setLoading(true);
    hideError();

    const formData = new FormData();

    formData.append(
        "image",
        selectedFile
    );

    try {

        const response = await fetch(
            "/analyze",
            {
                method: "POST",
                body: formData
            }
        );


        if (!response.ok) {

            let message = "Something went wrong while analyzing the image.";

            try {

                const errorData = await response.json();

                if (errorData.detail) {
                    message = errorData.detail;
                }

            } catch {
                // Keep default message
            }

            throw new Error(message);
        }


        const result = await response.json();

        displayResults(result);


    } catch (error) {

        showError(error.message);

    } finally {

        setLoading(false);

    }

});


/* --------------------------------
   DISPLAY RESULTS
-------------------------------- */

function displayResults(result) {

    emptyResults.classList.add("hidden");
    resultContent.classList.remove("hidden");

    resultStatus.classList.remove("hidden");


    if (
        result.status === "unknown_meal" ||
        !result.meal_recognized
    ) {

        resultTitle.textContent =
            "We couldn't recognize this meal";

        resultStatus.textContent =
            "Not recognized";

        caloriesValue.textContent = "—";
        proteinValue.textContent = "—";
        carbsValue.textContent = "—";
        fatValue.textContent = "—";

        ingredientsBody.replaceChildren();

        showWarnings(
            result.warnings?.length
                ? result.warnings
                : ["Try uploading a clearer photo of the meal."]
        );

        return;
    }


    resultTitle.textContent =
        "Meal analysis";

    resultStatus.textContent =
        result.status === "completed_with_warnings"
            ? "Completed with warnings"
            : "Analysis complete";


    const totals = result.totals || {};


    caloriesValue.textContent =
        `${formatNumber(totals.kcal)} kcal`;

    proteinValue.textContent =
        `${formatNumber(totals.protein_g)} g`;

    carbsValue.textContent =
        `${formatNumber(totals.carbs_g)} g`;

    fatValue.textContent =
        `${formatNumber(totals.fat_g)} g`;


    

    updateHeroPreview(result);

renderIngredients(
        result.ingredients || []
    );


    showWarnings(
        result.warnings || []
    );
}


/* --------------------------------
   INGREDIENT TABLE
-------------------------------- */

function renderIngredients(items) {

    ingredientsBody.replaceChildren();


    items.forEach(item => {

        const ingredient = item.ingredient || {};
        const nutrition = item.nutrition;

        const row = document.createElement("tr");


        const values = [

            ingredient.name || "Unknown",

            ingredient.estimated_grams !== undefined
                ? `${formatNumber(ingredient.estimated_grams)} g`
                : "—",

            ingredient.confidence !== undefined
                ? `${Math.round(ingredient.confidence * 100)}%`
                : "—",

            nutrition
                ? `${formatNumber(nutrition.kcal)} kcal`
                : "—",

            nutrition
                ? `${formatNumber(nutrition.protein_g)} g`
                : "—",

            nutrition
                ? `${formatNumber(nutrition.carbs_g)} g`
                : "—",

            nutrition
                ? `${formatNumber(nutrition.fat_g)} g`
                : "—"

        ];


        values.forEach(value => {

            const cell = document.createElement("td");

            cell.textContent = value;

            row.appendChild(cell);

        });


        ingredientsBody.appendChild(row);

    });

}


/* --------------------------------
   WARNINGS
-------------------------------- */

function showWarnings(warnings) {

    if (!warnings || warnings.length === 0) {

        warningsBox.classList.add("hidden");

        warningsBox.textContent = "";

        return;
    }


    warningsBox.replaceChildren();


    warnings.forEach(warning => {

        const item = document.createElement("div");

        item.textContent = `⚠ ${warning}`;

        warningsBox.appendChild(item);

    });


    warningsBox.classList.remove("hidden");
}


/* --------------------------------
   LOADING
-------------------------------- */

function setLoading(isLoading) {

    if (isLoading) {

        analyzeButton.disabled = true;

        buttonText.textContent =
            "Analyzing meal...";

        loader.classList.remove("hidden");

    } else {

        analyzeButton.disabled =
            !selectedFile;

        buttonText.textContent =
            "Analyze Meal";

        loader.classList.add("hidden");

    }

}


/* --------------------------------
   ERROR
-------------------------------- */

function showError(message) {

    errorMessage.textContent = message;

    errorMessage.classList.remove("hidden");
}


function hideError() {

    errorMessage.textContent = "";

    errorMessage.classList.add("hidden");
}


/* --------------------------------
   HELPERS
-------------------------------- */

function formatNumber(value) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toFixed(1);
}

/* --------------------------------
   HERO LATEST ANALYSIS
-------------------------------- */

function updateHeroPreview(result) {

    if (!result || !result.totals) {
        return;
    }

    const totals = result.totals;

    const calories =
        document.getElementById("heroCaloriesValue");

    const protein =
        document.getElementById("heroProteinValue");

    const carbs =
        document.getElementById("heroCarbsValue");

    const fat =
        document.getElementById("heroFatValue");

    const badge =
        document.getElementById("heroPreviewBadge");

    const image =
        document.getElementById("heroPreviewImage");


    if (calories) {
        calories.textContent =
            `${formatNumber(totals.kcal)} kcal`;
    }

    if (protein) {
        protein.textContent =
            `${formatNumber(totals.protein_g)} g`;
    }

    if (carbs) {
        carbs.textContent =
            `${formatNumber(totals.carbs_g)} g`;
    }

    if (fat) {
        fat.textContent =
            `${formatNumber(totals.fat_g)} g`;
    }

    if (badge) {
        badge.textContent = "Latest analysis";
    }

    if (image && selectedFile) {

        if (image.dataset.objectUrl) {
            URL.revokeObjectURL(
                image.dataset.objectUrl
            );
        }

        const objectUrl =
            URL.createObjectURL(selectedFile);

        image.src = objectUrl;
        image.dataset.objectUrl = objectUrl;
    }
}
