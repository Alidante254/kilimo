const express = require("express");
const PORT = process.env.PORT || 3001;
const cors = require("cors");
require("dotenv").config();
const openai = require("./src/ai.js");

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors());

app.get("/", (_req, res) => res.send("Welcome, MamaPesa\n"));

app.post("/ussd", async (req, res) => {
  const { text } = req.body;
  let response = "";
  const textParts = text.split("*");

  if (text === "") {
    response =
      "CON Welcome, MamaPesa\n1. Save for an asset\n2. Loans\n3. Chat with pesa AI\n4. Pay to till\n5. Deposit funds\n0. Exit";
  } else if (
    textParts[0] === "1" ||
    textParts[0] === "2" ||
    textParts[0] === "3" ||
    textParts[0] === "4" ||
    textParts[0] === "5"
  ) {
    const selectedOption = textParts[0];

    if (textParts.length > 1) {
      const question = textParts[1];
      try {
        const outcome = await openai.askAboutAgriculture(question);
        response = `END ${outcome}`;
      } catch (error) {
        response =
          "END An error occurred while processing your request. Please try again.";
      }
    } else {
      // Modify the prompt based on the selected option
      switch (selectedOption) {
        case "1":
          response = "CON Enter asset name:\n 0. Back\n";
          break;
        case "2":
          response = "CON 1. Request loan\n2. Repay loan\n0. Back\n";
          break;
        case "3":
          if (textParts.length > 1) {
            const question = textParts.slice(1).join(" ");
            try {
              const outcome = await openai.askAboutAgriculture(question);
              response = `END ${outcome}`;
            } catch (error) {
              response =
                "END An error occurred while processing your request. Please try again.";
            }
          } else {
            response =
              "CON Please chat with pesa AI by asking any question:\n 0. Back\n";
          }
          break;
        case "4":
          response = "CON Enter till number:\n 0. Back\n";
          break;
        case "5":
          response = "CON Enter amount:\n 0. Back\n";
          break;
        default:
          response = "CON Invalid option. Please try again. \n 0. Back\n";
          break;
      }
    }
  } else if (text === "0") {
    response =
      "CON Welcome, MamaPesa\n1. Save for an asset\n2. Loans\n3. Chat with pesa AI\n4. Pay to till\n5. Deposit funds\n0. Exit";
  } else {
    response = "END Invalid input. Please try again.";
  }

  res.set("Content-Type", "text/plain");
  res.send(response);
});

app.use("*", (_req, res) =>
  res.status(400).send("Invalid route. Please check your URL and try again.")
);

app.listen(PORT, () => {
  console.log(`App is running on port ${PORT}`);
});
