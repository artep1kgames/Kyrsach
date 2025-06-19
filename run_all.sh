#!/bin/bash
(cd backend && python3 -m uvicorn main:app --reload) &
(cd frontend && python3 -m http.server 5000) &
wait