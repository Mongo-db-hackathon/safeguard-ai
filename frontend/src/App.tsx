import React, { useState } from 'react';
import './App.css';

export default function App() {
  const [message, setMessage] = useState(''); // input text
  const [loading, setLoading] = useState(false); // optional loading state

  // Function to send message to backend
  const handleSend = async () => {
    if (!message.trim()) return; // don't send empty message

    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      console.log('✅ Backend response:', data);
    } catch (err) {
      console.error('❌ Error sending message:', err);
    } finally {
      setLoading(false);
      setMessage(''); // clear input
    }
  };

  // Allow "Enter" key to send
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div className="app">
      {/* Top Header */}
      <header className="header">
        <div className="product-name">Product Name</div>
        <button className="sign-in">Sign In</button>
      </header>

      {/* Main Layout */}
      <div className="main">
        {/* Left: Chat */}
        <aside className="chat">
          <div className="chat-title">AI Assistant</div>

          <div className="chat-messages">
            <div className="chat-bubble">
              Hello! I'm here to help you with the video. Feel free to ask any questions!
            </div>
          </div>

          <div className="chat-input">
            <input
              type="text"
              placeholder={loading ? 'Sending...' : 'Ask a question...'}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button className="send" onClick={handleSend} disabled={loading}>
              ➤
            </button>
          </div>
        </aside>

        {/* Right: Video Section */}
        <section className="video">
          <video controls width="100%">
            <source src="https://www.w3schools.com/html/mov_bbb.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <h3>Video Title</h3>
        </section>
      </div>
    </div>
  );
}
