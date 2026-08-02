// ---------- 1. LIBRARIES ----------
// load express library and put it in a variable
// require(): reads the package out of node_modules/ and hands you the library as an object
const express = require('express');
const mongoose = require('mongoose');

// ---------- 2. APP + CONFIG ----------
// create the application
const app = express();
const port = process.env.PORT || 3000;
// mongodb:// : the protocol, like http://
// localhost: where Mongo is. Your machine, right now
// 27017: the port you published with -p 27017:27017
// /todos: the database name. Mongo creates it automatically on first write; you don't set it up
const mongoUrl = process.env.MONGO_URL || 'mongodb://localhost:27017/todos';

// ---------- 3. MIDDLEWARE ----------
// express.json() is middleware - runs on every request before routes and parses a JSON request body into req.body
app.use(express.json());

// ---------- 4. SCHEMA + MODEL ----------
// the schema is a blueprint - describes a todo's shape
const todoSchema = new mongoose.Schema({
  // required: true means Mongoose refuses to save without a title
  title: {type: String, required: true},
  // default: false fills in completed automatically, replacing the completed: false
  completed: {type: Boolean, default: false},
});

// the model is the working tool built from that blueprint - a machine that reads and writes documents matching it
// all your database calls go through Todo
// Mongoose lowercases and pluralizes 'Todo' into a collection named todos, automatically
const Todo = mongoose.model('Todo', todoSchema);

// ---------- 5. ROUTES ----------
// async on every handler
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// async(): means this function contains waiting
app.get('/todos', async (req, res) => {
  // Database calls go over a network - microsecs, but not instant.
  // await pauses this one request until the answer comes back, while Node keeps serving other requests meanwhile
  // Miss an await and you send a Promise object to the client instead of your data

  // Todo.find(): no arguments means "everything", returning an array
  const todos = await Todo.find();
  // a database query
  res.json(todos);
});

app.post('/todos', async (req, res) => {
  const {title} = req.body;
  // 400: you sent bad data
  if (!title) return res.status(400).json({error: 'title is required'});

  // Todo.create({title}): builds and saves in one step, returning the saved document with the _id Mongo assigned
  // pass only title because completed has a schema default and _id is Mongo's job
  const todo = await Todo.create({title});
  // 201: created
  res.status(201).json(todo);
});

app.get('/todos/:id', async (req, res) => {
  const todo = await Todo.findById(req.params.id);
  // 404: no such thing
  if (!todo) return res.status(404).json({error: 'not found'});
  res.json(todo);
});

// only overwrite fields the client actually sent
app.put('/todos/:id', async (req, res) => {
  const {title, completed} = req.body;

  const update = {};
  
  // check for presence, not truthiness
  if (title !== undefined) update.title = title;
  if (completed !== undefined) update.completed = completed;

  // findByIdAndUpdate(id, update, options) takes 3 arguments:
  // - the id
  // - the update object you built from only the fields the client sent - same "check presence, not truthiness" logic you already wrote, 
  // just collected into an object instead of mutating in place, because the change has to travel to the database as 1 instruction
  // - options:
  //  + new: true - return the document after the update. Default is false, which returns the old version.
  //        You'd update correctly but show stale data to the client, and the bug looks like the update failed
  //  + runValidation: true - re-check schema rules on update. Off by default
  const todo = await Todo.findByIdAndUpdate(req.params.id, update, {
    new: true,
    runValidators: true,
  });

  if (!todo) return res.status(404).json({error: 'not found'});
  res.json(todo);
});

app.delete('/todos/:id', async (req, res) => {
  // findByIdAndDelete: returns the deleted document, or null if there was nothing there (you're checking "did i actually delete sth?")
  const todo = await Todo.findByIdAndDelete(req.params.id);
  if (!todo) return res.status(404).json({error: 'not found'});

  // 204: success with no body to send
  res.status(204).end();
});

// Expressidentifies error handlers by counting parameters - 4 means error handler, 3 means normal middleware
// ---------- 6. ERROR HANDLER ----------

// next must stay in the signature even though you don't call it; 
// delete it and Express silently treats this as a normal middleware that never runs (strange API)
app.use((err, req, res, next) => {
  // CastError -> malformed id -> 400, client's fault
  if (err.name === 'CastError') return res.status(400).json({error: 'invalid id'});
  // ValidationError -> broke a schema rule -> 400, client's fault
  if (err.name === 'ValidationError') return res.status(400).json({error: err.message});
  console.error(err);
  // anything else -> 500, and console.error(err) so you can see it
  res.status(500).json({error: 'server error'});
});

// ---------- 7. CONNECT, THEN START ----------

// mongoose.connect() returns a promise - 'I'll finish later'
mongoose.connect(mongoUrl)
  // .then() runs on success
  .then(() => {
    // connect first, accept traffic second
    console.log('Connected to MongoDB');
    // actually start the server and wait for request
    // the function runs once, when startup succeeds
    app.listen(port, () => {
      console.log(`Server listening on port ${port}`);
    });
  })
  // .catch() runs on failure
  .catch((err) => {
    console.error('Failed to connect to MongoDB:', err.message);
    // kills process if connection fails
    // 1 means "exited with an error" - 0 means success
    process.exit(1);
  });


