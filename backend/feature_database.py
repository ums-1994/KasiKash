# Comprehensive feature database for KasiKash chatbot App Mode
# This covers all app features and functions with detailed explanations

FEATURE_DATABASE = {
    # === CORE APP FEATURES ===
    'dashboard': {
        'description': "Your main hub showing balance, recent activities, and quick access to all features",
        'how_to': "Access from the main menu - shows your financial overview, recent transactions, and quick actions",
        'keywords': ['dashboard', 'home', 'main', 'overview', 'summary']
    },
    
    'stokvel': {
        'description': "Community savings groups where members contribute regularly and can request payouts",
        'how_to': "Go to Stokvels → Create New Stokvel → Fill details → Add members → Start contributing",
        'keywords': ['stokvel', 'stokvels', 'group', 'savings', 'community', 'create stokvel', 'new stokvel']
    },
    
    'contributions': {
        'description': "Payments you make to your stokvels - track history and make new contributions",
        'how_to': "Go to Contributions → Select stokvel → Enter amount → Choose payment method → Submit",
        'keywords': ['contribution', 'contributions', 'pay', 'payment', 'contribute', 'deposit']
    },
    
    'payouts': {
        'description': "Request money from your stokvel - may need admin approval depending on rules",
        'how_to': "Go to Payouts → Select stokvel → Enter amount → Provide reason → Submit request",
        'keywords': ['payout', 'payouts', 'withdraw', 'request money', 'get money', 'cash out']
    },
    
    'savings goals': {
        'description': "Personal financial targets you set and track progress towards",
        'how_to': "Go to Savings Goals → Create New Goal → Set target amount and deadline → Start saving",
        'keywords': ['savings goal', 'savings goals', 'goal', 'target', 'save', 'personal savings']
    },
    
    'profile': {
        'description': "Your personal information, total contributions, active stokvels, and KYC documents",
        'how_to': "Access from menu → Update details, upload profile picture, submit KYC documents",
        'keywords': ['profile', 'account', 'personal', 'information', 'details', 'kyc']
    },
    
    'settings': {
        'description': "Manage account preferences, language, notifications, and security settings",
        'how_to': "Go to Settings → Configure language, notifications, security, and account preferences",
        'keywords': ['settings', 'preferences', 'configuration', 'account settings', 'options']
    },
    
    'notifications': {
        'description': "Stay updated on important activities like contributions, payouts, and system messages",
        'how_to': "Click the bell icon → View all notifications → Mark as read/unread",
        'keywords': ['notification', 'notifications', 'alerts', 'messages', 'updates']
    },
    
    'payment methods': {
        'description': "Manage your bank accounts, cards, and other payment options for contributions",
        'how_to': "Go to Payment Methods → Add new method → Set as default → Use for contributions",
        'keywords': ['payment method', 'payment methods', 'bank', 'card', 'payment options']
    },
    
    'financial analysis': {
        'description': "Charts and graphs showing your spending habits and financial health over time",
        'how_to': "Access from menu → View spending patterns, income analysis, and financial insights",
        'keywords': ['financial analysis', 'analysis', 'charts', 'graphs', 'spending', 'insights']
    },
    
    'loans': {
        'description': "Request loans from stokvels based on their rules and your contribution history",
        'how_to': "Go to Request Loan → Select stokvel → Enter amount and reason → Submit for approval",
        'keywords': ['loan', 'loans', 'borrow', 'request loan', 'borrow money']
    },
    
    'kyc': {
        'description': "Know Your Customer verification - upload ID and proof of address for verification",
        'how_to': "Go to Profile → Upload KYC Documents → Submit ID and proof of address → Wait for approval",
        'keywords': ['kyc', 'verification', 'identity', 'documents', 'verify', 'proof']
    },
    
    'statements': {
        'description': "Download detailed PDF statements for your stokvels showing all transactions",
        'how_to': "Go to stokvel page → Click Download Statement → Get PDF with all transaction history",
        'keywords': ['statement', 'statements', 'download', 'pdf', 'transaction history']
    },
    
    'members': {
        'description': "Manage stokvel members - add, remove, view roles and contribution history",
        'how_to': "Go to stokvel → Manage Members → Add/remove members → Set roles → View activity",
        'keywords': ['members', 'member', 'add member', 'remove member', 'manage members']
    },
    
    'referrals': {
        'description': "Invite friends to join KasiKash and earn rewards for successful referrals",
        'how_to': "Go to Referrals → Share your referral link → Track successful invites → Earn rewards",
        'keywords': ['referral', 'referrals', 'invite', 'invite friends', 'share']
    },
    
    'virtual rewards': {
        'description': "Earn points and rewards for using KasiKash features and completing activities",
        'how_to': "Use app features → Earn points → Redeem rewards → Track your progress",
        'keywords': ['rewards', 'points', 'virtual rewards', 'earn', 'redeem']
    },
    
    'marketplace': {
        'description': "Browse and purchase products from community vendors and local businesses",
        'how_to': "Go to Marketplace → Browse categories → Select products → Place orders → Track delivery",
        'keywords': ['marketplace', 'shop', 'buy', 'products', 'vendors', 'local']
    },
    
    # === ADMIN FEATURES ===
    'admin': {
        'description': "Admin panel for managing users, approving loans/KYC, creating events, and sending notifications",
        'how_to': "Access admin panel → Manage platform users → Approve requests → Create events → Send notifications",
        'keywords': ['admin', 'administrator', 'admin panel', 'management']
    },
    
    'admin dashboard': {
        'description': "High-level overview of platform statistics, pending approvals, and system health",
        'how_to': "Admin panel → Dashboard → View total users, stokvels, pending approvals, and analytics",
        'keywords': ['admin dashboard', 'admin overview', 'statistics', 'analytics']
    },
    
    'manage users': {
        'description': "View, search, and manage all users on the platform including adding new users",
        'how_to': "Admin panel → Manage Users → Search users → View details → Edit permissions → Add new users",
        'keywords': ['manage users', 'user management', 'all users', 'search users']
    },
    
    'loan approvals': {
        'description': "Review, approve, or reject loan requests made by users with detailed history",
        'how_to': "Admin panel → Loan Approvals → Review requests → Approve/reject → View history",
        'keywords': ['loan approval', 'loan approvals', 'approve loans', 'review loans']
    },
    
    'kyc approvals': {
        'description': "Review user-submitted KYC documents and approve or reject verification status",
        'how_to': "Admin panel → KYC Approvals → Review documents → Verify information → Approve/reject",
        'keywords': ['kyc approval', 'kyc approvals', 'verify documents', 'review kyc']
    },
    
    'admin events': {
        'description': "Create and manage events for specific stokvels and send notifications to members",
        'how_to': "Admin panel → Events → Create new event → Set details → Send notifications → Track attendance",
        'keywords': ['admin events', 'create events', 'manage events', 'event management']
    },
    
    'admin memberships': {
        'description': "Manage different pricing plans and membership tiers offered on the platform",
        'how_to': "Admin panel → Memberships → Create plans → Set pricing → Manage benefits → Track subscriptions",
        'keywords': ['admin memberships', 'membership plans', 'pricing', 'subscriptions']
    },
    
    'admin notifications': {
        'description': "Send custom broadcast notifications to all users or specific user groups",
        'how_to': "Admin panel → Notifications → Compose message → Select recipients → Send broadcast",
        'keywords': ['admin notifications', 'send notifications', 'broadcast', 'announcements']
    },
    
    'admin settings': {
        'description': "Configure platform-wide settings, system preferences, and global configurations",
        'how_to': "Admin panel → Settings → Configure system settings → Update preferences → Save changes",
        'keywords': ['admin settings', 'platform settings', 'system configuration']
    },
    
    # === FINANCIAL ADVISOR FEATURES ===
    'financial advisor': {
        'description': "AI-powered financial analysis and advice based on your bank statements and spending patterns",
        'how_to': "Go to Financial Advisor → Upload bank statement → Get AI analysis → Chat with advisor → View insights",
        'keywords': ['financial advisor', 'advisor', 'financial advice', 'ai advisor', 'money advice']
    },
    
    'upload statement': {
        'description': "Upload your bank statements for AI analysis and personalized financial advice",
        'how_to': "Financial Advisor → Upload Statement → Select file → Submit for analysis → View results",
        'keywords': ['upload statement', 'bank statement', 'upload', 'statement analysis']
    },
    
    'chat advisor': {
        'description': "Interactive chat with AI financial advisor for personalized money management advice",
        'how_to': "Financial Advisor → Chat → Ask questions → Get personalized advice → Track conversation",
        'keywords': ['chat advisor', 'ai chat', 'financial chat', 'money chat', 'advisor chat']
    },
    
    'budget insights': {
        'description': "AI-generated insights about your spending patterns and budget recommendations",
        'how_to': "Financial Advisor → Insights → View spending analysis → Get budget tips → Track improvements",
        'keywords': ['budget insights', 'spending insights', 'budget advice', 'money insights']
    },
    
    'financial goals': {
        'description': "Set and track financial goals with AI-powered recommendations and progress tracking",
        'how_to': "Financial Advisor → Goals → Create financial goals → Get AI recommendations → Track progress",
        'keywords': ['financial goals', 'money goals', 'financial planning', 'goal setting']
    },
    
    # === SUPPORT & HELP ===
    'help': {
        'description': "Get help with any KasiKash feature, troubleshoot issues, and find answers",
        'how_to': "Use this chatbot, contact support, or check the help documentation",
        'keywords': ['help', 'support', 'assistance', 'troubleshoot', 'problem', 'issue']
    },
    
    'contact support': {
        'description': "Reach out to KasiKash support team for technical issues or account problems",
        'how_to': "Go to Contact page → Fill form → Describe issue → Submit → Get response",
        'keywords': ['contact support', 'support', 'contact', 'help desk', 'customer service']
    },
    
    'pricing': {
        'description': "View different membership plans, pricing tiers, and their benefits",
        'how_to': "Go to Pricing page → Compare plans → Choose membership → Subscribe to features",
        'keywords': ['pricing', 'plans', 'membership', 'subscription', 'cost', 'price']
    },
    
    'about': {
        'description': "Learn about KasiKash mission, team, and community-focused financial services",
        'how_to': "Go to About page → Read about our mission → Learn about the team → Understand our values",
        'keywords': ['about', 'mission', 'team', 'company', 'story']
    }
}

# Helper function to find the best matching feature
def find_feature_match(user_message):
    """
    Find the best matching feature based on user message keywords
    Returns the feature key and confidence score
    """
    user_words = user_message.lower().split()
    best_match = None
    best_score = 0
    
    for feature_key, feature_data in FEATURE_DATABASE.items():
        keywords = feature_data.get('keywords', [])
        
        # Check exact keyword matches
        for keyword in keywords:
            if keyword in user_message.lower():
                return feature_key, 1.0  # Exact match
        
        # Check partial matches
        for keyword in keywords:
            for word in user_words:
                if keyword in word or word in keyword:
                    score = len(set(keyword.split()) & set(word.split())) / max(len(keyword.split()), len(word.split()))
                    if score > best_score:
                        best_score = score
                        best_match = feature_key
    
    return best_match, best_score

# Helper function to get feature response
def get_feature_response(feature_key):
    """
    Get a comprehensive response for a specific feature
    """
    if feature_key not in FEATURE_DATABASE:
        return None
    
    feature = FEATURE_DATABASE[feature_key]
    response = f"**{feature_key.title()}**\n\n"
    response += f"**What it is:** {feature['description']}\n\n"
    response += f"**How to use it:** {feature['how_to']}\n\n"
    response += "💡 **Tip:** You can access this feature from the main menu or ask me for more specific help!"
    
    return response 