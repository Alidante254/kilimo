//const { OpenAIApi } = require("openai");
const axios = require('axios');
require('dotenv').config();

/*const configuration = new OpenAIApi.Configuration({
  apiKey: process.env.OA_API_KEY,
});*/
const apiKey= process.env.OA_API_KEY;
//const openai = new OpenAIApi(configuration);

const askAboutAgriculture = (question) => {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'This assistant is trained on answering questions related to Mamapesa.'
        },
        {
          role: 'user',
          content: `${question}`
        }
      ],
      temperature: 0.7,
      max_tokens: 150
    });

    const config = {
      method: 'post',
      maxBodyLength: Infinity,
      url: 'https://api.openai.com/v1/chat/completions',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      data
    };

    axios.request(config)
      .then((response) => {
        const answer = response.data.choices[0].message.content.trim();
        resolve(answer);
      })
      .catch((error) => {
        console.error('Axios Error:', error.message);
        if (error.response) {
          console.error('Status Code:', error.response.status);
          console.error('Response Data:', error.response.data);
        }
        reject(error);
      });
  });
};

module.exports = {
  askAboutAgriculture: askAboutAgriculture
};