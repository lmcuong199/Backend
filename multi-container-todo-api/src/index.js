// load express library and put it in a variable
const express = require('express');

// create the application
const app = express();
const port = process.env.PORT || 3000;

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// express.json() is middleware - runs on every request before routes and parses a JSON request body into req.body
app.use(express.json());

// lives in memory, so it resets every restart
let todos = []; 
let nextId = 1;

app.get('/todos', (req, res) => {
  // convert array into JSON string
  // set the Content-Type: application/json header
  // send it
  res.json(todos);
});

app.post('/todos', (req, res) => {
  const {title} = req.body;
  // 400: you sent bad data
  if (!title) return res.status(400).json({error: 'title is required'});

  const todo = {id: nextId++, title, completed:false};
  todos.push(todo);
  // 201: created
  res.status(201).json(todo);
});

app.get('/todos/:id', (req, res) => {
  const todo = todos.find(t => t.id === Number(req.params.id));
  // 404: no such thing
  if (!todo) return res.status(404).json({error: 'not found'});
  res.json(todo);
});

// only overwrite fields the client actually sent
app.put('/todos/:id', (req, res) => {
  const todo = todos.find(t => t.id === Number(req.params.id));
  if (!todo) return res.status(404).json({error: 'not found'});

  const {title, completed} = req.body;
  // check for presence, not truthiness
  if (title !== undefined) todo.title = title;
  if (completed !== undefined) todo.completed = completed;
  res.json(todo);
});

app.delete('/todos/:id', (req, res) => {
  const index = todos.findIndex(t => t.id === Number(req.params.id));
  if (index === -1) return res.status(404).json({error: 'not found'});

  // remove 1 element starting at index, modifying the array in place
  todos.splice(index, 1);
  // 204: success with no body to send
  res.status(204).end();
});

// actually start the server and wait for request
// the function runs once, when startup succeeds
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
