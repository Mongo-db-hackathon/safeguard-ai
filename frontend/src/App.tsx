import React, { useState, useRef, useEffect } from 'react';
import './App.css';

type Message = {
  sender: 'user' | 'bot';
  text: string;
  videoIndex?: number;
};

type VideoResult = {
  path: string;
  timestamp: number;
};

export default function App() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [videoResults, setVideoResults] = useState<VideoResult[]>([]);
  const [activeVideoIndex, setActiveVideoIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage: Message = { sender: 'user', text: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage('');
    inputRef.current?.focus();
    setLoading(true);

    setMessages((prev) => [...prev, { sender: 'bot', text: 'typing...' }]);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      const { reply, videos } = data;

      setMessages((prev) => {
        const withoutTyping = prev.filter((m) => m.text !== 'typing...');
        const botMessages: Message[] = [{ sender: 'bot', text: reply }];

        if (Array.isArray(videos)) {
          setVideoResults(videos);

          const videoMessages: Message[] = videos.map((v, i) => ({
            sender: 'bot',
            text: `Watch ${extractFileName(v.path)} at ${v.timestamp}s`,
            videoIndex: i,
          }));

          return [...withoutTyping, ...botMessages, ...videoMessages];
        } else {
          return [...withoutTyping, ...botMessages];
        }
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

  const handleVideoClick = (index: number) => {
    setActiveVideoIndex(index);
    setTimeout(() => {
      const ref = videoRef.current;
      if (ref && videoResults[index]) {
        ref.currentTime = videoResults[index].timestamp;
      }
    }, 500);
  };

  const extractFileName = (path: string) => {
    return path.split('/').pop() || '';
  };

  return (
    <div className="app" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="header">
        <div className="product-name" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img
            src="/safeguardai.svg"
            alt="Safeguard AI Logo"
            style={{ width: '28px', height: '28px' }}
          />
          <span>Safeguard AI</span>
        </div>
      </header>

      <div className="main" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <aside className="chat" style={{ overflowY: 'auto' }}>
          {/* <div className="chat-title">AI Assistant</div> */}

          <div className="chat-messages">
            <div className="chat-bubble bot">
              Please ask a question and I will help find relevant video clips.
            </div>

            {messages.map((msg, i) =>
              msg.videoIndex !== undefined ? (
                <div key={i} className="video-card-wrapper">
                  <div className="video-card">
                    <div className="video-card-title">
                      {extractFileName(videoResults[msg.videoIndex].path)} at{' '}
                      {videoResults[msg.videoIndex].timestamp}s
                    </div>
                    <button
                      onClick={() => handleVideoClick(msg.videoIndex!)}
                      className="video-card-button"
                    >
                      Watch Now
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  key={i}
                  className={`chat-bubble ${msg.sender === 'user' ? 'user' : 'bot'} ${
                    msg.text === 'typing...' ? 'typing' : ''
                  }`}
                >
                  {msg.text === 'typing...' ? <span className="dots">...</span> : msg.text}
                </div>
              )
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <input
              ref={inputRef}
              type="text"
              placeholder={loading ? 'Waiting for reply...' : 'Ask a question'}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={false}
            />
            <button
              className="send"
              onClick={handleSend}
              style={{
                backgroundColor: '#000',
                border: 'none',
                padding: '8px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img
                src="/search.svg"
                alt="send"
                style={{
                  width: '18px',
                  height: '18px',
                  filter: 'invert(1)',
                }}
              />
            </button>
          </div>
        </aside>

        <section className="video" style={{ overflowY: 'auto', flex: 1, padding: '1rem' }}>
          {activeVideoIndex !== null && videoResults[activeVideoIndex] ? (
            <div>
              <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%' }}>
                <video
                  ref={videoRef}
                  controls
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                  }}
                >
                  <source
                    src={`http://127.0.0.1:5000/videos/${extractFileName(
                      videoResults[activeVideoIndex].path
                    )}`}
                    type="video/mp4"
                  />
                  Your browser does not support the video tag.
                </video>
              </div>

              <h3>{extractFileName(videoResults[activeVideoIndex].path)}</h3>
            </div>
          ) : (
            <div
              style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                color: '#888',
              }}
            >
              <p style={{ marginTop: '1rem' }}>Select a result to play a video</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
