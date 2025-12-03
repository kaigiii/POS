document.addEventListener('DOMContentLoaded', ()=>{
    const toggle = document.getElementById('navToggle');
    const nav = document.querySelector('.nav-links');
    if(!toggle || !nav) return;

    const closeNav = ()=>{
        nav.classList.remove('open');
        toggle.classList.remove('active');
    };

    toggle.addEventListener('click', (e)=>{
        e.stopPropagation();
        nav.classList.toggle('open');
        toggle.classList.toggle('active');
    });

    // Close when clicking a link
    nav.addEventListener('click', (e)=>{
        const target = e.target.closest('a');
        if(target) closeNav();
    });

    // Close when clicking outside
    document.addEventListener('click', (e)=>{
        if(!nav.classList.contains('open')) return;
        if(e.target.closest('.nav-links') || e.target.closest('.hamburger')) return;
        closeNav();
    });

    // Close on Escape
    document.addEventListener('keydown', (e)=>{
        if(e.key === 'Escape') closeNav();
    });
});
