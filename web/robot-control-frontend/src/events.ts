// src/event.ts

export type EventMeta = {
    name: string;
    generated_t: number;
    eid: number;
};

export type ServerEvent = EventMeta;

export type BrowserEvent = EventMeta & {
    received_t: number;
};

export type ConfirmType = 'ok' | 'cancel' | 'both';

export type ConfirmRequestEvent = ServerEvent & {
    name: 'confirm_request';
    msg: string;
    require_confirm: ConfirmType;
};

export type ConfirmResponseEvent = BrowserEvent & {
    name: 'confirm_response';
    respond_to_eid: number;
    response: ConfirmType;
};

export type AnyServerEvent = ConfirmRequestEvent;

export function parseServerEvent(json: string): ConfirmRequestEvent {
    const base = JSON.parse(json) as ServerEvent;
    const received_t = Date.now();
    // unknown assertion because TS cannot verify
    const evt = { ...base, received_t } as unknown as ConfirmRequestEvent;

    if (evt.name !== 'confirm_request') {
        throw new Error(`Expected confirm_request, got ${evt.name}`);
    }
    return evt;
}

export function nextEid(): number {
    nextEid.eid++;
    return nextEid.eid;
}

export namespace nextEid {
    export let eid = 0;
}
