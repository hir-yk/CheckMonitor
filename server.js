const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

// Simulating API Handling
app.get('/api/data', (req, res) => {
    res.json({message: 'API is working!'});
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});