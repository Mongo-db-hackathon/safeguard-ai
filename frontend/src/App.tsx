import React, { useState, useRef, useEffect } from 'react';
import './App.css';

type Message = {
  sender: 'user' | 'bot';
  text: string;
};

export default function App() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null); // ✅ to keep focus

  // ✅ auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ✅ keep focus on input after sending
  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage: Message = { sender: 'user', text: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage('');
    inputRef.current?.focus(); // ✅ immediately refocus after sending
    setLoading(true);

    // show typing indicator
    setMessages((prev) => [...prev, { sender: 'bot', text: 'typing...' }]);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();

      // remove typing indicator and add bot reply
      setMessages((prev) => {
        const withoutTyping = prev.filter((m) => m.text !== 'typing...');
        return [...withoutTyping, { sender: 'bot', text: data.reply }];
      });
    } catch (err) {
      console.error('❌ Error sending message:', err);
      setMessages((prev) => [
        ...prev.filter((m) => m.text !== 'typing...'),
        { sender: 'bot', text: '⚠️ Connection error. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div className="app">
      {/* Top Header */}
      <header className="header">
        <div className="product-name">Safeguard AI</div>
        <button className="sign-in">Sign In</button>
      </header>

      <div className="main">
        {/* Chat Section */}
        <aside className="chat">
          <div className="chat-title">AI Assistant</div>

          <div className="chat-messages">
            {/* Intro bubble */}
            <div className="chat-bubble bot">
              Hello! I'm here to help you with the video. Feel free to ask any questions!
            </div>

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-bubble ${msg.sender === 'user' ? 'user' : 'bot'} ${
                  msg.text === 'typing...' ? 'typing' : ''
                }`}
              >
                {msg.text === 'typing...' ? <span className="dots">...</span> : msg.text}
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <input
              ref={inputRef} // ✅ keeps focus
              type="text"
              placeholder={loading ? 'Waiting for reply...' : 'Ask a question...'}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={false} // ✅ user can always type
            />
            <button className="send" onClick={handleSend}>
              ➤
            </button>
          </div>
        </aside>

        {/* Video Section */}
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
