---
id: "CATArena/CATArena_-_bridgegame_bridge_magic_develop_instruction"
company: "CATArena"
product: "CATArena - bridgegame bridge magic develop instruction"
category: "coding-agents"
annotation: "ai"
source_file: "bridgegame_bridge_magic_develop_instruction.md"
---

# Bridge AI Development Guide

You are a professional AI developer who needs to develop an intelligent AI for the bridge battle environment. Please carefully read the following development instructions and implement a high-performance bridge AI according to the requirements.

## Environment Overview

This is a standard bridge battle environment based on HTTP with the following characteristics:

### Game Server
- **Port**: 9031 (default)
- **Game Type**: 4-player bridge (2v2 battles)
- **Game Phases**: Bidding phase → Playing phase
- **Scoring System**: Standard bridge scoring rules

## Development Requirements

### 1. AI Service Interface Specification

Your AI must implement the following HTTP interfaces:

#### Health Check
```
GET /health
Response: {"status": "healthy", "ai_id": "your_AI_ID", "active_games": 0}
```

#### AI Information
```
GET /info
Response: {"ai_id": "your_AI_ID", "name": "AI_name", "version": "1.0", "description": "description", "capabilities": ["capability_list"]}
```

#### Join Game
```
POST /join_game
Request: {"game_id": "game_ID", "player_id": 0, "player_name": "AI_name"}
Response: {"status": "joined", "ai_id": "your_AI_ID", "game_id": "game_ID", "player_id": 0}
```

#### Get Action
```
POST /get_action
Request: {"game_id": "game_ID", "player_id": 0, "game_state": {...}}
Response: {"action": {...}, "ai_id": "your_AI_ID", "game_id": "game_ID", "reasoning": "decision_reasoning"}
```

#### Leave Game
```
POST /leave_game
Request: {"game_id": "game_ID"}
Response: {"status": "left", "ai_id": "your_AI_ID", "game_id": "game_ID"}
```

### 2. Game Understanding

#### Key API Interfaces
The game server provides the following key interfaces:

```
GET http://localhost:9031/games/{game_id}/state?player_id={player_id}
POST http://localhost:9031/games/{game_id}/call
POST http://localhost:9031/games/{game_id}/play
GET http://localhost:9031/games/{game_id}/legal_actions?player_id={player_id}
```

### 3. Development Steps

#### Step 1: Environment Preparation
1. Create AI service files
2. Implement Flask application and basic interfaces
3. Ensure HTTP service can start correctly

#### Step 2: Source Code Analysis
1. **Carefully read `server.py`**: Understand the core logic and rules of the game
2. **Analyze `bridge_ai_server.py`**: Understand the basic implementation of AI service
3. **Study API responses**: Understand various data structures through testing
4. **Understand game state**: Analyze state management in bidding and playing phases

#### Step 3: Core Algorithm Implementation
1. **Bidding strategy**: Implement bidding algorithm based on point count and hand pattern
2. **Playing strategy**: Implement playing algorithm based on game situation
3. **Partner coordination**: Implement coordination strategy with partner
4. **Situation evaluation**: Implement accurate situation evaluation algorithm

#### Step 4: Testing and Validation
1. Start game server: `python -m bridge.server --port 51086`
2. Start your AI service: Ensure your AI service runs on the specified port and correctly implements HTTP interfaces
3. Run tests: `python test_ai_client.py`

### 4. Key Development Tips

#### Algorithm Design Principles
- Implement accurate point count calculation (high card points + distribution points)
- Implement intelligent bidding strategy
- Implement efficient playing algorithm
- Consider partner coordination and signal passing
- Optimize algorithm efficiency

#### Common AI Strategies
1. **Point evaluation**: Calculate hand points (A=4, K=3, Q=2, J=1)
2. **Hand pattern evaluation**: Evaluate hand distribution and fit potential
3. **Bidding strategy**: Choose appropriate bids based on points and hand pattern
4. **Playing strategy**: Choose optimal plays based on game situation
5. **Partner coordination**: Coordinate with partner through signal passing

#### Bidding Strategy Points
- **Opening**: 13+ points to open, choose appropriate bids
- **Responding**: Choose appropriate responses based on partner's bids
- **Competitive bidding**: Choose appropriate competitive bids when opponents bid
- **Preemptive bidding**: Use preemptive bids at appropriate times

#### Playing Strategy Points
- **Opening lead**: Choose appropriate opening leads
- **Following**: Choose appropriate plays based on game situation
- **Trump management**: Use trumps reasonably
- **Signals**: Pass signals to partner through plays

#### Error Handling
- Gracefully handle various exception situations
- Ensure AI works normally in various situations
- Implement reasonable timeout and retry mechanisms

### 5. Performance Requirements

- **Response time**: Each action should complete within 10 seconds
- **Memory usage**: Reasonably control memory usage
- **Error handling**: Gracefully handle various exception situations
- **Concurrency support**: Support participating in multiple games simultaneously

### 6. Testing Requirements

Your AI must pass the following tests:
1. Health check test
2. Basic functionality test
3. Game rule adaptation test
4. Bidding strategy test
5. Playing strategy test
6. Battle test

### 7. Submission Requirements

Please provide:
1. Complete AI service code
2. Startup instructions
3. Algorithm description
4. Test results
5. Performance analysis

## Development Tips

1. **Deep source code analysis**: Carefully read `server.py` and `bridge_ai_server.py` to understand specific implementations
2. **Understand game mechanics**: Understand core rules and mechanisms of bridge through source code analysis
3. **Test-driven development**: Implement basic functionality first, then optimize step by step
4. **Error handling**: Ensure AI works normally in various exception situations
5. **Performance optimization**: Optimize algorithm efficiency while ensuring correctness

## Evaluation Criteria

Your AI will be evaluated based on the following criteria:
1. **Correctness**: Whether it correctly follows bridge rules
2. **Intelligence**: Quality of AI decisions
3. **Stability**: Performance in various situations
4. **Performance**: Response speed and resource usage
5. **Code quality**: Readability and maintainability of code

## Technical Reference

### Data Structures
- **Card representation**: Suit (C/D/H/S) + Rank (2-9/T/J/Q/K/A)
- **Hand**: Collection of 13 cards
- **Bidding history**: Record all bidding actions
- **Playing history**: Record all playing actions
- **Game state**: Record current phase, player status, and other information

### Key Algorithms
- **Point calculation**: High card points + distribution points
- **Bidding evaluation**: Bidding decisions based on points and hand pattern
- **Playing evaluation**: Playing decisions based on game situation
- **Situation evaluation**: Evaluate current situation and winning probability

## Important Reminders

**Please carefully read the source code**: The specific implementation logic of the game is all in `server.py`. Through deep analysis of the source code, you can:
- Understand the core logic of the game
- Learn about bidding and playing rules
- Master data structure design
- Learn error handling mechanisms

**Reference example code**: `bridge_ai_server.py` provides a complete AI service implementation example that can serve as a reference for development.

**Bridge uniqueness**: Bridge is a 4-player cooperative game that requires consideration of:
- Partner coordination
- Signal passing
- Situation evaluation
- Risk control

Please begin your development work and ensure your AI can perform excellently in this standard bridge environment!
