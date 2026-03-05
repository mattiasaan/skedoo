import { useState } from "react";
import { COLORS } from "../../constants/colors";
import { communityPosts, TAG_COLORS, classLeaderboard } from "../../data/community";
import Icon from "../ui/Icon";

export default function CommunityScreen() {
  const [liked,     setLiked]     = useState({});
  const [activeTab, setActiveTab] = useState("feed");

  const toggleLike = (id) =>
    setLiked(prev => ({ ...prev, [id]: !prev[id] }));

  return (
    <div className="anim-fadeIn" style={{ flex: 1, overflowY: "auto" }}>

      {/* ── Header ──────────────────────────────── */}
      <div style={{ padding: "20px 20px 0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Community</h2>
          <button style={newPostBtnStyle}>
            <Icon name="plus" size={14} color={COLORS.greenLight} /> New Post
          </button>
        </div>

        {/* Tabs */}
        <TabSwitcher active={activeTab} onChange={setActiveTab} />

        {/* Leaderboard banner */}
        <LeaderboardBanner data={classLeaderboard} />
      </div>

      {/* ── Posts ───────────────────────────────── */}
      <div style={{ padding: "0 20px", display: "flex", flexDirection: "column", gap: 14 }}>
        {communityPosts.map(post => (
          <PostCard
            key={post.id}
            post={post}
            liked={!!liked[post.id]}
            onLike={() => toggleLike(post.id)}
          />
        ))}
        <div style={{ height: 20 }} />
      </div>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function TabSwitcher({ active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 4, marginBottom: 20, background: COLORS.bgCard, borderRadius: 12, padding: 4 }}>
      {[
        { id: "feed",     label: "📰 Feed"     },
        { id: "trending", label: "🔥 Trending" },
      ].map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          style={{
            flex:       1,
            padding:    "9px",
            borderRadius: 9,
            border:     "none",
            cursor:     "pointer",
            fontSize:   13,
            fontWeight: 700,
            background: active === tab.id ? COLORS.green : "transparent",
            color:      active === tab.id ? "white" : COLORS.textMuted,
            transition: "all 0.2s",
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function LeaderboardBanner({ data }) {
  return (
    <div style={{ background: "linear-gradient(135deg, #1a2a4a, #0d1a2e)", border: `1px solid ${COLORS.blue}30`, borderRadius: 16, padding: "16px", marginBottom: 20, display: "flex", alignItems: "center", gap: 14 }}>
      <div style={{ width: 44, height: 44, background: `${COLORS.orange}20`, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Icon name="trophy" size={22} color={COLORS.orange} />
      </div>
      <div style={{ flex: 1 }}>
        <p style={{ margin: "0 0 2px", fontWeight: 700, fontSize: 14 }}>
          {data.className} · #{data.rank} in Leaderboard
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ flex: 1, height: 4, background: "#1a2a4a", borderRadius: 2 }}>
            <div style={{ width: `${data.progress * 100}%`, height: "100%", background: COLORS.blue, borderRadius: 2 }} />
          </div>
          <span style={{ fontSize: 12, color: COLORS.textMuted }}>{data.points} pts</span>
        </div>
      </div>
    </div>
  );
}

function PostCard({ post, liked, onLike }) {
  return (
    <div
      style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: "18px", transition: "border-color 0.2s" }}
      onMouseEnter={e => e.currentTarget.style.borderColor = COLORS.textDim}
      onMouseLeave={e => e.currentTarget.style.borderColor = COLORS.border}
    >
      {/* Author row */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <div style={avatarStyle}>{post.avatar}</div>
        <div>
          <p style={{ margin: 0, fontWeight: 700, fontSize: 14 }}>{post.author}</p>
          <p style={{ margin: 0, fontSize: 12, color: COLORS.textDim }}>{post.time}</p>
        </div>
        <button style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer" }}>
          <Icon name="flag" size={16} color={COLORS.textDim} />
        </button>
      </div>

      {/* Body */}
      <p style={{ margin: "0 0 12px", fontSize: 14, lineHeight: 1.6 }}>{post.text}</p>

      {/* Tags */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
        {post.tags.map(tag => (
          <span key={tag} style={{ background: `${TAG_COLORS[tag] || COLORS.textDim}20`, color: TAG_COLORS[tag] || COLORS.textDim, fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 6 }}>
            #{tag}
          </span>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 16, borderTop: `1px solid ${COLORS.border}`, paddingTop: 12 }}>
        <ActionBtn
          icon="heart"
          color={liked ? COLORS.red : COLORS.textDim}
          label={post.likes + (liked ? 1 : 0)}
          onClick={onLike}
        />
        <ActionBtn icon="hash" color={COLORS.textDim} label={`${post.comments} comments`} />
      </div>
    </div>
  );
}

function ActionBtn({ icon, color, label, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{ display: "flex", alignItems: "center", gap: 6, background: "none", border: "none", cursor: "pointer", color, fontSize: 13, fontWeight: 600 }}
    >
      <Icon name={icon} size={16} color={color} />
      {label}
    </button>
  );
}

/* ── Style objects ───────────────────────────────────────────────────────── */
const avatarStyle = {
  width:          38,
  height:         38,
  borderRadius:   "50%",
  background:     `linear-gradient(135deg, ${COLORS.green}, ${COLORS.greenDark})`,
  display:        "flex",
  alignItems:     "center",
  justifyContent: "center",
  fontSize:       13,
  fontWeight:     700,
  flexShrink:     0,
};

const newPostBtnStyle = {
  background:   `${COLORS.green}20`,
  border:       `1px solid ${COLORS.green}40`,
  borderRadius: 10,
  padding:      "8px 14px",
  color:        COLORS.greenLight,
  fontSize:     13,
  fontWeight:   600,
  cursor:       "pointer",
  display:      "flex",
  alignItems:   "center",
  gap:          6,
};
