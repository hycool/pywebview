(function () {
    const cef = {};
    const customEventMap = {
        windowCloseEvent: {
            name: 'windowCloseEvent',
            event: new CustomEvent('windowCloseEvent', { detail: { windowId: window.windowId } }),
            hooks: 0
        }
    };
    cef.dispatchCustomEvent = (eventName) => {
        if (customEventMap[eventName].hooks === 0 &&
            window["windowInstance"] &&
            typeof window["windowInstance"]["closeWindow"] === 'function') {
            window["windowInstance"]["closeWindow"]();
        } else {
            window.dispatchEvent(customEventMap[eventName].event)
        }
    };
    cef.addEventListener = (eventName, eventHook) => {
        if (customEventMap[eventName] === undefined) {
            console.error(`window.__cef__.addEventListener(eventName, eventHook) : eventName 必须是 ${Object.keys(customEventMap)} 中的一个`)
            return;
        }
        if (typeof eventHook !== 'function') {
            console.error('window.__cef__.addEventListener(eventName, eventHook): eventHook 必须是一个函数');
            return;
        }
        customEventMap[eventName].hooks += 1;
        window.addEventListener(eventName, eventHook);
    };
    cef.removeEventListener = (eventName, eventHook) => {
        if (customEventMap[eventName] === undefined) {
            console.error(`window.__cef__.addEventListener(eventName, eventHook) : eventName 必须是 ${Object.keys(customEventMap)} 中的一个`)
            return;
        }
        if (typeof eventHook !== 'function') {
            console.error('window.__cef__.addEventListener(eventName, eventHook): eventHook 必须是一个函数');
            return;
        }
        customEventMap[eventName].hooks -= 1;
        window.removeEventListener(eventName, eventHook);
    };
    window.__cef__ = cef;
} ());