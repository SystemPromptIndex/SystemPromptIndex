---
id: "CATArena/CATArena_-_gomokugame_gomoku_develop_instruction"
company: "CATArena"
product: "CATArena - gomokugame gomoku develop instruction"
category: "coding-agents"
source_file: "gomokugame_gomoku_develop_instruction.md"
---

# Gomoku AI Development Guide

You are a professional AI developer who needs to develop an intelligent AI for the Gomoku battle environment. Please carefully read the following development instructions and implement a high-performance Gomoku AI according to the requirements.

## Environment Overview

This is a standard Gomoku battle environment based on HTTP with the following characteristics:

### Game Server
- **Port**: 9000 (default)

## Development Requirements

### 1. AI Service Interface Specification

Your AI must implement the following HTTP interfaces:

#### Health Check
```
GET /health
Response: {"status": "healthy", "ai_id": "your_AI_ID", "active_games": 0}
```

#### AI Info
```
GET /info
Response: {"ai_id": "your_AI_ID", "name": "AI_name", "version": "1.0", "description": "description", "capabilities": ["capabilities_list"]}
```

#### Join Game
```
POST /join_game
Request: {"game_id": "gameID", "my_color": "black/white", "game_server_url": "http://localhost:9000"}
Response: {"status": "joined", "ai_id": "your_AI_ID", "game_id": "gameID", "my_color": "color"}
```

#### Get Move
```
POST /get_move
Request: {"game_id": "gameID", "board": [[board_state]], "current_player": "black/white"}
Response: {"move": [x, y], "ai_id": "your_AI_ID", "game_id": "gameID", "reasoning": "move_reason"}
```

#### Leave Game
```
POST /leave_game
Request: {"game_id": "gameID"}
Response: {"status": "left", "ai_id": "your_AI_ID", "game_id": "gameID"}
```

### 2. Game Rule Understanding

#### Board Representation
- `0`: Empty position
- `1`: Black stone
- `2`: White stone

#### Key API Interfaces
The game server provides the following key interfaces:

```
GET http://localhost:10000/games/{game_id}/state
POST http://localhost:10000/games/{game_id}/move
GET http://localhost:10000/games/{game_id}/history
```

### 3. Development Steps

#### Step 1: Environment Preparation
1. Create AI service file
2. Implement Flask application and basic interfaces
3. Ensure HTTP service can start correctly

#### Step 2: Source Code Analysis
1. **Carefully read `server.py`**: Understand the core logic and rules of the game
2. **Analyze `ai_http_server.py`**: Understand the basic implementation of AI service
3. **Study API responses**: Understand various data structures through testing

#### Step 3: Core Algorithm Implementation
1. **Rule Adaptation**: Implement standard Gomoku game logic
2. **Strategy Design**: Design AI strategy based on Gomoku rules
3. **Algorithm Optimization**: Implement efficient decision algorithms

#### Step 4: Testing and Validation
1. Start game server: `python server.py --port 10000`
2. Start your AI service: Ensure your AI service runs on the specified port and correctly implements HTTP interfaces
3. Run testing: `python test_ai_client.py`

### 4. Key Development Tips

#### Algorithm Design Principles
- Implement winning priority strategy
- Implement defense priority strategy
- Implement threat detection and building
- Consider balance between offense and defense
- Optimize algorithm efficiency

#### Common AI Strategies
1. **Winning Priority**: Find positions that can directly win
2. **Defense Priority**: Prevent opponent from winning
3. **Threat Building**: Find positions that can form threats
4. **Position Evaluation**: Evaluate strategic value of each position
5. **Search Algorithms**: Use Minimax, Alpha-Beta pruning, etc.

#### Error Handling
- Gracefully handle various abnormal situations
- Ensure AI can work normally in various situations
- Implement reasonable timeout and retry mechanisms

### 5. Performance Requirements

- **Response Time**: Each move should be completed within 5 seconds
- **Memory Usage**: Reasonably control memory usage
- **Error Handling**: Gracefully handle various abnormal situations
- **Concurrent Support**: Support participating in multiple games simultaneously

### 6. Testing Requirements

Your AI must pass the following tests:
1. Health check testing
2. Basic feature testing
3. Game rule adaptation testing
4. Battle testing

### 7. Submission Requirements

Please provide:
1. Complete AI service code
2. Startup instructions
3. Algorithm explanation
4. Testing results
5. Performance analysis

## Development Tips

1. **Deep Source Code Analysis**: Carefully read `server.py` and `ai_http_server.py` to understand specific implementations
2. **Understand Game Mechanisms**: Understand the core rules and mechanisms of the game through source code analysis
3. **Testing-Driven Development**: First implement basic features, then gradually optimize
4. **Error Handling**: Ensure AI can work normally in various abnormal situations
5. **Performance Optimization**: Optimize algorithm efficiency while ensuring correctness

## Evaluation Standards

Your AI will be evaluated according to the following standards:
1. **Correctness**: Whether it correctly follows Gomoku rules
2. **Intelligence**: Quality of AI decisions
3. **Stability**: Performance in various situations
4. **Performance**: Response speed and resource usage
5. **Code Quality**: Readability and maintainability of code

## Technical Reference

### Data Structures
- **Board Representation**: 2D array representing board state
- **Direction Vectors**: Used for detecting consecutive stones
- **Game State**: Record current player, game status, etc.

## Important Reminders

**Please carefully read the source code**: All specific implementation logic of the game is in `server.py`. Through deep source code analysis, you can:
- Understand the core logic of the game
- Learn win/loss determination algorithms
- Master data structure design
- Learn error handling mechanisms

**Reference Example Code**: `ai_http_server.py` provides a complete AI service implementation example that can serve as a reference for development.

Please start your development work and ensure your AI can perform excellently in this standard Gomoku environment!
