#!/bin/bash
(cd backend && python3 -m uvicorn backend.app.main:app --reload) &
(cd frontend && python3 -m http.server 5000) &
wait