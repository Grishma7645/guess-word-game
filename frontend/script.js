// frontend/script.js

// ---------- Auth: Register & Login ----------
async function registerUser() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const res = await fetch("/register", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });
  const out = document.getElementById("msg");
  const data = await res.json();
  if (res.ok) {
    out.textContent = "Registered successfully. Now login.";
  } else {
    out.textContent = data.detail || JSON.stringify(data);
  }
}

async function loginUser() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const res = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("username", data.username);
    if (data.role === "admin") {
      window.location.href = "/admin";
    } else {
      window.location.href = "/play";
    }
  } else {
    document.getElementById("msg").textContent = data.detail || JSON.stringify(data);
  }
}

function logoutUser() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  localStorage.removeItem("game_id");
  window.location.href = "/";
}

// ---------- Game page functions ----------
async function startGame() {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Not logged in");
    return;
  }
  const res = await fetch("/start_game", { 
    method: "POST", 
    headers: { "Authorization": "Bearer " + token } 
  });
  const data = await res.json();
  if (!res.ok) {
    alert(data.detail || JSON.stringify(data));
    return;
  }
  localStorage.setItem("game_id", data.game_id);
  document.getElementById("gameId").textContent = "Game ID: " + data.game_id;
  buildEmptyBoard();
  document.getElementById("guessControls").style.display = "block";
}

function buildEmptyBoard() {
  const board = document.getElementById("board");
  board.innerHTML = "";
  for (let r = 0; r < 5; r++) {
    const row = document.createElement("div");
    row.className = "row";
    for (let c = 0; c < 5; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = "";
      row.appendChild(cell);
    }
    board.appendChild(row);
  }
}

async function submitGuess() {
  const token = localStorage.getItem("token");
  const game_id = parseInt(localStorage.getItem("game_id"));
  const guess = document.getElementById("guessInput").value.toUpperCase();
  if (!guess || guess.length !== 5) { 
    alert("Enter 5 letters"); 
    return; 
  }
  const res = await fetch("/guess", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify({ game_id, guess })
  });
  const data = await res.json();
  if (!res.ok) {
    alert(data.detail || JSON.stringify(data));
    return;
  }
  renderGuessRow(guess, data.feedback);
  document.getElementById("guessInput").value = "";
  if (!data.is_active) {
    if (data.is_won) {
      alert("🎉 Congratulations — You won!");
    } else {
      alert("❌ Better luck next time.");
    }
    document.getElementById("guessControls").style.display = "none";
  }
}

function renderGuessRow(guess, feedback) {
  const board = document.getElementById("board");
  const rows = board.querySelectorAll(".row");
  let rowToFill = null;
  for (let r of rows) {
    const firstCell = r.children[0];
    if (firstCell.textContent === "") { 
      rowToFill = r; 
      break; 
    }
  }
  if (!rowToFill) return;
  for (let i = 0; i < 5; i++) {
    const cell = rowToFill.children[i];
    cell.textContent = guess[i];
    cell.classList.remove("absent","present","correct");
    if (feedback[i] === "correct") cell.classList.add("correct");
    else if (feedback[i] === "present") cell.classList.add("present");
    else cell.classList.add("absent");
  }
}
