const SECTIONS = {
  1: {
    title: "Two Move Mates",
    folder: "puzzles/1",
    firstPuzzle: 1,
    lastPuzzle: 136,
  },
  2: {
    title: "Three Move Mates",
    folder: "puzzles/2",
    firstPuzzle: 137,
    lastPuzzle: 417,
  },
  3: {
    title: "Four Move Mates",
    folder: "puzzles/3",
    firstPuzzle: 418,
    lastPuzzle: 546,
  },
};

const app = document.getElementById("app");

function getParams() {
  const params = new URLSearchParams(window.location.search);

  return {
    section: params.get("section"),
    puzzle: Number(params.get("puzzle") || 1),
    view: params.get("view") || "puzzle",
  };
}

function pageUrl(section, puzzle, view = "puzzle") {
  return `?section=${section}&puzzle=${puzzle}&view=${view}`;
}

function clampPuzzle(sectionData, puzzle) {
  return Math.max(
    sectionData.firstPuzzle,
    Math.min(sectionData.lastPuzzle, puzzle)
  );
}

function paddedNumber(number) {
  return String(number).padStart(3, "0");
}

function makeImageWithFallback(sectionData, puzzle, type) {
  const img = document.createElement("img");
  img.className = type === "puzzle" ? "puzzle-image" : "solution-image";
  img.alt = `Puzzle ${puzzle} ${type}`;

  const candidates = [
    `${sectionData.folder}/${puzzle}_${type}.png`,
    `${sectionData.folder}/${paddedNumber(puzzle)}_${type}.png`,
  ];

  let index = 0;

  img.src = candidates[index];

  img.onerror = () => {
    index += 1;

    if (index < candidates.length) {
      img.src = candidates[index];
    } else {
      img.remove();

      const error = document.createElement("div");
      error.className = "error";
      error.textContent = `Could not find ${type} image for puzzle ${puzzle}.`;

      document.querySelector(".image-wrap").appendChild(error);
    }
  };

  return img;
}

function renderHome() {
  app.innerHTML = `
    <div class="main-page">
      <h1>Sam Loyd Chess Problems</h1>

      <a class="section-card" href="${pageUrl(1, 1)}">
        Two Move Mates
      </a>

      <a class="section-card" href="${pageUrl(2, 1)}">
        Three Move Mates
      </a>

      <a class="section-card" href="${pageUrl(3, 1)}">
        Four Move Mates
      </a>
    </div>
  `;
}

function renderPuzzlePage(sectionId, puzzle, view) {
  const sectionData = SECTIONS[sectionId];

  if (!sectionData) {
    renderHome();
    return;
  }

  const currentPuzzle = clampPuzzle(sectionData, puzzle);
  const isSolution = view === "solution";

  const minus10 = clampPuzzle(sectionData, currentPuzzle - 10);
  const minus1 = clampPuzzle(sectionData, currentPuzzle - 1);
  const plus1 = clampPuzzle(sectionData, currentPuzzle + 1);
  const plus10 = clampPuzzle(sectionData, currentPuzzle + 10);

  app.innerHTML = `
    <div class="puzzle-page">
      <div class="top-bar">
        <a class="home-link" href="./">← Home</a>
        <div class="section-title">${sectionData.title}</div>
      </div>

      <div class="puzzle-number">No. ${currentPuzzle}</div>

      <div class="image-wrap"></div>

      ${
        isSolution
          ? `<a class="action-button" href="${pageUrl(sectionId, currentPuzzle, "puzzle")}">Back to Puzzle</a>`
          : `<a class="action-button" href="${pageUrl(sectionId, currentPuzzle, "solution")}">Show Solution</a>`
      }

      <div class="nav-left">
        <a class="nav-button" href="${pageUrl(sectionId, minus10, "puzzle")}">−10</a>
        <a class="nav-button" href="${pageUrl(sectionId, minus1, "puzzle")}">−1</a>
      </div>

      <div class="nav-right">
        <a class="nav-button" href="${pageUrl(sectionId, plus1, "puzzle")}">+1</a>
        <a class="nav-button" href="${pageUrl(sectionId, plus10, "puzzle")}">+10</a>
      </div>
    </div>
  `;

  const imageWrap = document.querySelector(".image-wrap");
  const image = makeImageWithFallback(
    sectionData,
    currentPuzzle,
    isSolution ? "solution" : "puzzle"
  );

  imageWrap.appendChild(image);
}

function render() {
  const { section, puzzle, view } = getParams();

  if (!section) {
    renderHome();
    return;
  }

  renderPuzzlePage(section, puzzle, view);
}

render();
