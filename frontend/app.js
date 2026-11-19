document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentLang = 'ar';
    let conversationHistory = [];
    let chartInstances = {};
    let chartCounter = 0;

    // Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesList = document.getElementById('messages-list');
    const welcomeCard = document.getElementById('welcome-card');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const langArBtn = document.getElementById('lang-ar-btn');
    const langEnBtn = document.getElementById('lang-en-btn');
    const ingestionModalBtn = document.getElementById('ingestion-modal-btn');
    const ingestionModal = document.getElementById('ingestion-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');

    // UI Translation Strings
    const UI_STRINGS = {
        ar: {
            title: "مساعد المعرفة لأهداف التنمية المستدامة في مصر",
            subtitle: "استكشف تقارير توطين أهداف التنمية المستدامة الرسمية الصادرة عن وزارة التخطيط والتنمية الاقتصادية",
            placeholder: "اسأل سؤالاً عن أي محافظة أو مؤشر أممي في التقارير الرسمية...",
            clearText: "مسح",
            kbStatsText: "55 تقريراً",
            officialBadge: "🏛️ مصدر رسمي معتمد",
            welcomeTitle: "مرحباً بك في المنصة الذكية لتقارير التنمية المستدامة",
            welcomeDesc: "يتيح هذا المساعد التفاعلي للمشاركين في العرض التقديمي الاستفسار عن المؤشرات والإحصاءات والمستهدفات الخاصة بمحافظات مصر الـ 27، والمقارنة بين الإصدار الأول (2021) والإصدار الثاني (2024) وتقرير الملخص العام وفق منهجية منظمة التعاون الاقتصادي والتنمية (OECD).",
            suggestedHeading: "💡 أسئلة استرشادية مقترحة:",
            footerNote: "📌 يتم الاعتماد حصرياً على البيانات الرسمية لتقارير توطين أهداف التنمية المستدامة بوزارة التخطيط والتنمية الاقتصادية.",
            citationsTitle: "📚 المراجع الرسمية من التقارير:",
            downloadPdf: "تحميل التقرير الرسمي PDF",
            page: "ص",
            edition1: "الإصدار الأول (2021)",
            edition2: "الإصدار الثاني (2024)",
            summaryReport: "تقرير الملخص العام (OECD)"
        },
        en: {
            title: "Egypt SDGs Knowledge Assistant",
            subtitle: "Explore Egypt's Sustainable Development Goals through official governorate reports (MPED)",
            placeholder: "Ask about any governorate, SDG indicator, or 2030 target...",
            clearText: "Clear",
            kbStatsText: "55 Reports",
            officialBadge: "🏛️ Official Government Source",
            welcomeTitle: "Welcome to Egypt SDGs Knowledge Assistant",
            welcomeDesc: "Interact directly with official SDG Localization Reports across Egypt's 27 governorates. Compare Edition 1 (2021) and Edition 2 (2024), analyze localized targets, and review OECD composite index scores.",
            suggestedHeading: "💡 Suggested Presentation Inquiries:",
            footerNote: "📌 Powered strictly by official data from the Ministry of Planning and Economic Development localization reports.",
            citationsTitle: "📚 Official Report Citations:",
            downloadPdf: "Download Official PDF",
            page: "P.",
            edition1: "First Edition (2021)",
            edition2: "Second Edition (2024)",
            summaryReport: "OECD Summary Report"
        }
    };

    function setLanguage(lang) {
        currentLang = lang;
        const html = document.documentElement;
        html.setAttribute('lang', lang);
        html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');

        if (lang === 'ar') {
            langArBtn.classList.add('active');
            langEnBtn.classList.remove('active');
        } else {
            langEnBtn.classList.add('active');
            langArBtn.classList.remove('active');
        }

        const s = UI_STRINGS[lang];
        document.getElementById('app-title').textContent = s.title;
        document.getElementById('app-subtitle').textContent = s.subtitle;
        userInput.placeholder = s.placeholder;
        document.getElementById('clear-text').textContent = s.clearText;
        document.getElementById('kb-stats-text').textContent = s.kbStatsText;
        document.getElementById('badge-official').textContent = s.officialBadge;
        document.getElementById('welcome-title').textContent = s.welcomeTitle;
        document.getElementById('welcome-desc').innerHTML = s.welcomeDesc;
        document.getElementById('suggested-heading').textContent = s.suggestedHeading;
        document.getElementById('footer-note').textContent = s.footerNote;

        // Update suggested chips text
        document.querySelectorAll('.suggested-chip').forEach(chip => {
            const q = lang === 'ar' ? chip.getAttribute('data-question') : chip.getAttribute('data-question-en');
            chip.querySelector('.chip-text').textContent = q;
        });
    }

    langArBtn.addEventListener('click', () => setLanguage('ar'));
    langEnBtn.addEventListener('click', () => setLanguage('en'));

    // Modal Events
    ingestionModalBtn.addEventListener('click', () => ingestionModal.classList.remove('hidden'));
    closeModalBtn.addEventListener('click', () => ingestionModal.classList.add('hidden'));
    ingestionModal.addEventListener('click', (e) => {
        if (e.target === ingestionModal) ingestionModal.classList.add('hidden');
    });

    // Clear Chat
    clearChatBtn.addEventListener('click', () => {
        conversationHistory = [];
        messagesList.innerHTML = '';
        if (welcomeCard) {
            welcomeCard.style.display = 'block';
            messagesList.appendChild(welcomeCard);
        }
        Object.values(chartInstances).forEach(c => c.destroy());
        chartInstances = {};
    });

    // Auto-expand textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
    });

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Suggested Chips click
    document.addEventListener('click', (e) => {
        const chip = e.target.closest('.suggested-chip');
        if (chip) {
            const q = currentLang === 'ar' ? chip.getAttribute('data-question') : chip.getAttribute('data-question-en');
            submitQuery(q);
        }
        const followup = e.target.closest('.followup-btn');
        if (followup) {
            const q = followup.getAttribute('data-question');
            submitQuery(q);
        }
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (text) {
            submitQuery(text);
        }
    });

    function submitQuery(queryText) {
        if (!queryText) return;
        
        userInput.value = '';
        userInput.style.height = 'auto';

        if (welcomeCard && welcomeCard.parentNode) {
            welcomeCard.style.display = 'none';
        }

        // Render User Message
        appendMessage('user', queryText);

        // Render Typing Indicator
        const typingEl = appendTypingIndicator();
        messagesList.scrollTop = messagesList.scrollHeight;

        // Post to API
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: queryText,
                history: conversationHistory,
                language: currentLang
            })
        })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            typingEl.remove();
            appendAssistantResponse(data);
            
            conversationHistory.push({ role: 'user', content: queryText });
            conversationHistory.push({ role: 'assistant', content: data.answer });
            if (conversationHistory.length > 10) {
                conversationHistory = conversationHistory.slice(-10);
            }
        })
        .catch(err => {
            typingEl.remove();
            console.error('Chat error:', err);
            const errText = currentLang === 'ar' ? 
                'عذراً، حدث خطأ أثناء الاتصال بالخادم. يرجى المحاولة مرة أخرى.' : 
                'Sorry, an error occurred while connecting to the server. Please try again.';
            appendMessage('assistant', errText);
        });
    }

    function appendMessage(role, text) {
        const row = document.createElement('div');
        row.className = `message-row ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}`;
        avatar.textContent = role === 'user' ? '👤' : '🇪🇬';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;
        
        row.appendChild(avatar);
        row.appendChild(bubble);
        messagesList.appendChild(row);
        messagesList.scrollTop = messagesList.scrollHeight;
        return row;
    }

    function appendTypingIndicator() {
        const row = document.createElement('div');
        row.className = 'message-row assistant typing';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar assistant';
        avatar.textContent = '🇪🇬';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = '<div class="typing-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
        
        row.appendChild(avatar);
        row.appendChild(bubble);
        messagesList.appendChild(row);
        return row;
    }

    function appendAssistantResponse(data) {
        const row = document.createElement('div');
        row.className = 'message-row assistant';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar assistant';
        avatar.textContent = '🇪🇬';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // 1. Markdown Text
        const parsedHtml = marked.parse(data.answer);
        const textContainer = document.createElement('div');
        textContainer.innerHTML = parsedHtml;
        bubble.appendChild(textContainer);

        // 2. Table if available
        if (data.table && data.table.rows && data.table.rows.length > 0) {
            const tableWrap = document.createElement('div');
            tableWrap.className = 'comparison-table-wrapper';
            
            const tableEl = document.createElement('table');
            tableEl.className = 'comparison-table';
            
            const thead = document.createElement('thead');
            const trHead = document.createElement('tr');
            data.table.headers.forEach(h => {
                const th = document.createElement('th');
                th.textContent = h;
                trHead.appendChild(th);
            });
            thead.appendChild(trHead);
            tableEl.appendChild(thead);

            const tbody = document.createElement('tbody');
            data.table.rows.forEach(r => {
                const tr = document.createElement('tr');
                if (r.sdg_name) {
                    const td1 = document.createElement('td');
                    td1.innerHTML = `<strong>${r.sdg_name}</strong>`;
                    const td2 = document.createElement('td');
                    td2.textContent = r.gov1_score;
                    const td3 = document.createElement('td');
                    td3.textContent = r.gov2_score;
                    tr.appendChild(td1);
                    tr.appendChild(td2);
                    tr.appendChild(td3);
                } else if (r.governorate) {
                    const td1 = document.createElement('td');
                    td1.textContent = r.rank;
                    const td2 = document.createElement('td');
                    td2.innerHTML = `<strong>${r.governorate}</strong>`;
                    const td3 = document.createElement('td');
                    td3.textContent = r.score;
                    tr.appendChild(td1);
                    tr.appendChild(td2);
                    tr.appendChild(td3);
                }
                tbody.appendChild(tr);
            });
            tableEl.appendChild(tbody);
            tableWrap.appendChild(tableEl);
            bubble.appendChild(tableWrap);
        }

        // 3. Responsive Chart if available
        if (data.chart && data.chart.labels && data.chart.labels.length > 0) {
            chartCounter++;
            const chartBox = document.createElement('div');
            chartBox.className = 'chart-container-box';
            
            if (data.chart.title) {
                const cTitle = document.createElement('div');
                cTitle.className = 'chart-title';
                cTitle.textContent = data.chart.title;
                chartBox.appendChild(cTitle);
            }

            const canvasWrap = document.createElement('div');
            canvasWrap.className = 'chart-canvas-wrapper';
            
            const canvas = document.createElement('canvas');
            const canvasId = `chart-${chartCounter}`;
            canvas.id = canvasId;
            canvasWrap.appendChild(canvas);
            chartBox.appendChild(canvasWrap);
            bubble.appendChild(chartBox);

            // Responsive Chart.js configuration
            setTimeout(() => {
                const ctx = document.getElementById(canvasId);
                if (ctx) {
                    const isMobile = window.innerWidth < 640;
                    const isSmall = window.innerWidth < 420;

                    chartInstances[canvasId] = new Chart(ctx, {
                        type: data.chart.type || 'bar',
                        data: {
                            labels: data.chart.labels,
                            datasets: data.chart.datasets.map(ds => ({
                                ...ds,
                                borderRadius: 4,
                                maxBarThickness: isSmall ? 18 : (isMobile ? 24 : 38)
                            }))
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                legend: {
                                    position: 'top',
                                    labels: {
                                        boxWidth: 10,
                                        font: {
                                            family: 'Cairo, Inter, sans-serif',
                                            size: isSmall ? 10 : (isMobile ? 11 : 13)
                                        }
                                    }
                                },
                                tooltip: {
                                    titleFont: { family: 'Cairo, Inter, sans-serif' },
                                    bodyFont: { family: 'Cairo, Inter, sans-serif' },
                                    padding: 8,
                                    cornerRadius: 6
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100,
                                    ticks: {
                                        font: {
                                            family: 'Cairo, Inter, sans-serif',
                                            size: isSmall ? 9 : 11
                                        },
                                        stepSize: 20
                                    },
                                    grid: {
                                        color: '#f1f5f9'
                                    }
                                },
                                x: {
                                    ticks: {
                                        font: {
                                            family: 'Cairo, Inter, sans-serif',
                                            size: isSmall ? 9 : (isMobile ? 10 : 12)
                                        },
                                        maxRotation: isMobile ? 45 : 30,
                                        minRotation: isMobile ? 35 : 0,
                                        autoSkip: isMobile && data.chart.labels.length > 10
                                    },
                                    grid: {
                                        display: false
                                    }
                                }
                            }
                        }
                    });
                }
            }, 60);
        }

        // 4. Citations
        if (data.citations && data.citations.length > 0) {
            const citBox = document.createElement('div');
            citBox.className = 'citations-box';
            
            const citHeader = document.createElement('div');
            citHeader.className = 'citations-header';
            citHeader.innerHTML = `<span>📑</span> ${UI_STRINGS[currentLang].citationsTitle}`;
            citBox.appendChild(citHeader);

            const citList = document.createElement('div');
            citList.className = 'citations-list';
            
            data.citations.forEach(c => {
                const pill = document.createElement('a');
                pill.className = 'citation-pill';
                pill.href = c.url;
                pill.target = '_blank';
                pill.rel = 'noopener noreferrer';
                pill.title = `${UI_STRINGS[currentLang].downloadPdf} - ${c.report_name}`;
                pill.innerHTML = `🏛️ ${c.governorate} | ${c.edition_name} | ${UI_STRINGS[currentLang].page} ${c.page_number} ↗`;
                citList.appendChild(pill);
            });
            citBox.appendChild(citList);
            bubble.appendChild(citBox);
        }

        // 5. Follow-up Suggestions
        if (data.followups && data.followups.length > 0) {
            const followBox = document.createElement('div');
            followBox.className = 'followups-box';
            data.followups.forEach(f => {
                const fBtn = document.createElement('button');
                fBtn.className = 'followup-btn';
                fBtn.setAttribute('data-question', f);
                fBtn.textContent = f;
                followBox.appendChild(fBtn);
            });
            bubble.appendChild(followBox);
        }

        row.appendChild(avatar);
        row.appendChild(bubble);
        messagesList.appendChild(row);
        messagesList.scrollTop = messagesList.scrollHeight;
    }

    // Handle screen orientation & window resize smoothly
    window.addEventListener('resize', () => {
        Object.values(chartInstances).forEach(c => {
            if (c) c.resize();
        });
    });
});
