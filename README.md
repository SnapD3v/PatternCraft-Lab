# PatternCraft-Lab

## Project Description
**PatternCraft Lab** is an interactive learning platform that combines structured theory, AI-driven explanations, and dynamic task generation to teach programming principles (e.g., SOLID) and design patterns. It is aimed at beginners and intermediate learners, offering a game-like, context-aware environment for practicing code refactoring using selected patterns.

## What Does the Solution Include?
**1) Theoretical Foundation:**  
• Short lessons on principles and patterns with real-world analogies (e.g., "Abstract Factory is like an assembly line for object creation").  
• Code examples (both best and worst practices), diagrams, and video overviews.  
• Lists of additional websites and literature for further learning.

**2) AI Tutor (e.g., integration with DeepSeek R1):**  
• Adaptive explanations: Generates examples based on the user's level (e.g., "Explain the Liskov Substitution Principle using a character hierarchy in a game").

**3) Task Generator:**  
• Creates scenarios requiring multiple patterns to be applied (e.g., "Refactor this order processing system using Builder and Strategy").

**4) Context Memory:**  
• Maintains session context, preventing the loss of information while solving multiple tasks.

**5) Code Sandbox:**  
• Built-in IDE with hints, pattern templates, and code validation.

**6) Instant Solution Validation:**  
• AI analyzes the code and checks if the selected patterns are correctly applied, providing detailed feedback.

**7) Progress Tracker:**  
• Badges (e.g., "Factory Pattern Expert"), personalized recommendations, and weak point analytics.


## Goal

**Month 1: Research & Planning**

*1. Research & Analysis*  
- Understanding the target audience:  
• Conduct surveys among beginner and intermediate developers.  
• Analyze popular learning and gamification platforms.  
- Competitive analysis:  
• Study existing platforms (Udemy, Codecademy) to identify their strengths and weaknesses.  
- Technical analysis:  
• Define target technologies (React.js, microservices architecture).  
• Explore AI integration options (DeepSeek R1).

*2. Concept Development*  
- Create the platform architecture:  
• Identify key system components: frontend, backend, database.  
• Design user scenarios.  
- Define functional specifications:  
• Formulate requirements for each core feature (theory, AI tutor, code sandbox, progress tracker).

**Month 2: Prototype Development**

*1. UI Prototype Creation*  
- User Interface (UI/UX) Design:  
• Develop platform page mockups with a focus on user experience.  
• Implement interactive design elements.  
- Prototype Testing:  
• Gather feedback from potential users and make adjustments.

*2. Backend Development*  
- Initial microservice structure:  
• Implement basic APIs for user and session management.  
• Set up a database to store user progress and task history.  
- AI Tutor Integration:  
• Begin developing algorithms for generating examples and tasks based on user level.

**Month 3: Feature Development & Testing**

*1. Completing Feature Development*  
- Integration of all components:  
• Connect frontend and backend, ensuring seamless interaction.  
• Implement the code sandbox with hints and validation.  
- Feedback Mechanism Development:  
• Implement AI-powered solution validation and code analysis module.

*2. System Testing*  
- Usability Testing:  
• Identify and fix bugs by gathering user feedback.  
- Alpha Release:  
• Launch the platform for a limited user group to test real-world functionality and make necessary improvements.

*3. Launch Preparation*  
- Marketing Strategy Development:  
• Prepare promotional materials (webinars, ad campaigns).  
- Planning the Next Development Phase:  
• Define actions for enhancing features and introducing new patterns and principles to the platform.


## Outcome (Product)
**Final Result:** An interactive learning platform that combines structured theory, AI-driven explanations, and dynamic task generation to teach programming principles (e.g., SOLID) and design patterns.


## Success Metrics  
What parameters will define success?

**1) User Engagement**  
- *DAU/MAU Ratio:* >30% (high engagement).  
- *Avg. Session Duration:* >15 minutes (indicating engaging tasks).  
- *Task Completion Rate:* >70% (tasks are sufficiently challenging but solvable).

**2) Learning Outcomes**  
- *Pre/Post-Test Scores:* After completing the course and solving at least one task per topic, students should be familiar with 90% of programming patterns on LeetCode and be capable of solving any Middle-level task.  
- *User Reviews:* >85% agree with the statement, "I feel more confident applying patterns after using the platform."

**3) Technical Metrics**
- *Accuracy:* >90% correct solution validation (evaluated against an expert test set).
- *Response Time:* <2 seconds for task/feedback generation.
- *Viral Growth:* 25% of users join through referral links (built-in "invite a friend for collaborative problem-solving" system).

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Third-Party Components
This project uses the following AI model:
- **qwen2.5-coder-1.5b-instruct.Q8_0**: Licensed under the Apache License 2.0. Available at https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct.
- Other models accessed via OpenRouter are subject to their respective licenses or terms, as outlined at https://openrouter.ai/terms.