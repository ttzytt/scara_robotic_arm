// src/events.ts

export interface EventMeta {
    name: string;
    generated_t: number;
    eid: number;
}

export type ConfirmType = 'ok' | 'cancel' | 'both';

export interface ServerEvent extends EventMeta {
    received_t: number;
}

export interface BrowserEvent extends EventMeta {
    // No received_t here.
}

export interface ConfirmRequestEvent extends ServerEvent {
    name: 'confirm_request';
    msg: string;
    require_confirm: ConfirmType;
}

export interface ConfirmResponseEvent extends BrowserEvent {
    name: 'confirm_response';
    respond_to_eid: number;
    response: ConfirmType;
}

export interface GamepadBtn {
    pressed: boolean;
    value: number;
    touched: boolean;
}

export interface GamepadRawState extends BrowserEvent {
    name: 'gamepad_raw_state';
    id: string;
    index: number;
    axes: number[];
    buttons: GamepadBtn[];
}


// ------------------ Utility Functions ------------------

/**
 * Parse a JSON string from WebSocket into a ConfirmRequestEvent.
 * Throws an Error if the event name is not 'confirm_request'.
 * 
 * @param json raw JSON from the WebSocket
 * @returns a typed ConfirmRequestEvent
 */
export function parseServerEvent(json: string): ConfirmRequestEvent {
    const base = JSON.parse(json) as EventMeta & Partial<ConfirmRequestEvent>;
    if (base.name !== 'confirm_request') {
        throw new Error(`Expected confirm_request, got ${base.name}`);
    }
    base.received_t = Date.now(); // Fill in received_t for server events
    // We know it's ConfirmRequestEvent, but TS cannot verify at compile time:
    return base as ConfirmRequestEvent;
}

export function nextEid(): number {
    nextEid.eid++;
    return nextEid.eid;
}

export namespace nextEid {
    export let eid = 0;
}
  