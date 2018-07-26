(function () {
    const moduleName = 'windowInstance';
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
            window[moduleName] &&
            typeof window[moduleName]["closeWindow"] === 'function') {
            window[moduleName]["closeWindow"]();
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
    cef.console = (msg, type) => {
        switch (type) {
            case 'error':
                console.error(msg);
                break;
            case 'warn':
                console.warn(msg);
                break;
            default:
                console.log(msg);
                break;
        }
    };
    cef.initializeCustomizePayload = (payload) => {
        if (window[moduleName] === undefined) {
            window[moduleName] = {}
        }
        const instance = window[moduleName];
        instance.payload = {};
        Object.keys(payload).forEach(key => {
            instance.payload[key] = payload[key]
        })
    };
    cef.updateWindowInstance = (key, value) => {
        if (window[moduleName] === undefined) {
            window[moduleName] = {}
        }
        window[moduleName][key] = value;
    };
    window.__cef__ = cef;
} ());