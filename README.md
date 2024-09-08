  0. Install Docker
  
  1. Set This Directory to Working Directory with cd in Terminal
  2. To Build Docker "Stuff" Run Command:
      docker-compose up --build
  2.5 To Remove Docker "Stuff" Run Command:
      docker-compose down
  3. To Update Docker Images Run Command in (2.)
  
  We now have two docker images, each with a running container:
      server (as https://server:5000 or https://localhost:5000)
      process (as https://process:8000 or https://localhost:8000)
  Server runs the server, and process can run anything else... (to be called by server)
