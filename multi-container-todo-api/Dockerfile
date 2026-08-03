# node: the official Node.js image, Node and npm preinstalled
# 20: major version 20, matching your local v20.18.0. Always pin this
# node: latest means your build silently changes when a new Node come out, and so not very good
# alpine: Alpine Linux, a minimal distribution. about 50MB vs 350MB for the Debian-based default
FROM node:20-alpine

# set the working directory inside the container, creating it if needed
# /app is a convention, not a requirement
WORKDIR /app

# copies package.json and package-lock.json (the * matches both) from your folder into /app in the image
# layer caching: each Dockerfile instruction creates a layer - a saved snapshot. 
#               On rebuild, Docker reuses cached layers until it hits 1 whose inputs changed; from there down, everything reruns
# -> Order dependencies before source code. it's the single highest-value Docker habit, and this two-line split is why
COPY package*.json ./

# execute a command during the build, and the result is baked into the image
# npm ci rather than npm install - "ci" for continuous integration. 
#        installs strictly from package-lock.json, exactly the versions recorded, also wipes node_modules first
# --omit=dev skips devDependencies
RUN npm ci --omit=dev

# copy the rest
# first . = your project folder on Win
# second . = /app inside the image, courtesy of WORKDIR
# this is where .dockerignore earns its keep: node_modules is skipped, so the Linux-native packages that npm ci just installed don't get overwritten by your Win ones
COPY . .

# documentation. It does not publish anything
# it records "this app listens on 3000" as metadata for human and tools
EXPOSE 3000

# the default command when a container starts - not during build
# RUN happens at build time and is baked in
# CMD happens at run time
# npm start, not npm run dev - production runs plain node. No file watcher
# The array form matters. 
CMD ["npm", "start"]
