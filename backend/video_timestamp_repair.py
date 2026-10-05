"""普通 MP4 的无损流式时间戳修复；只修改内存中的 fMP4 分片。"""
import asyncio
import contextvars
from functools import partial
import os
import re
import struct
import subprocess


MAX_MOOV_BYTES = 64 * 1024 * 1024
MAX_SAMPLES = 2_000_000


async def run_in_thread(func, *args, **kwargs):
    """在线程池中执行同步操作并传递上下文，兼容 Python 3.8。"""
    loop = asyncio.get_running_loop()
    context = contextvars.copy_context()
    call = partial(context.run, func, *args, **kwargs)
    return await loop.run_in_executor(None, call)


def boxes(data):
    offset = 0
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('MP4 box 头不完整')
        size, kind = struct.unpack_from('>I4s', data, offset)
        header = 8
        if size == 1:
            if offset + 16 > len(data):
                raise ValueError('MP4 扩展 box 头不完整')
            size = struct.unpack_from('>Q', data, offset + 8)[0]
            header = 16
        elif size == 0:
            size = len(data) - offset
        if size < header or offset + size > len(data):
            raise ValueError('MP4 box 长度无效')
        yield offset, kind, data[offset + header:offset + size]
        offset += size


def child(data, kind):
    for _, name, payload in boxes(data):
        if name == kind:
            return payload
    raise ValueError(f'MP4 缺少 {kind.decode()} 表')


def box(kind, payload):
    return struct.pack('>I4s', len(payload) + 8, kind) + payload


def u32(data, offset=0):
    return struct.unpack_from('>I', data, offset)[0]


def read_moov(path):
    """只读取 moov，跳过媒体数据，避免将完整视频加载到内存。"""
    total = os.path.getsize(path)
    found = None
    fragmented = False
    with open(path, 'rb') as source:
        offset = 0
        while offset < total:
            source.seek(offset)
            header = source.read(8)
            if len(header) != 8:
                raise ValueError('MP4 顶层 box 头不完整')
            size, kind = struct.unpack('>I4s', header)
            header_size = 8
            if size == 1:
                extended = source.read(8)
                if len(extended) != 8:
                    raise ValueError('MP4 扩展 box 头不完整')
                size = struct.unpack('>Q', extended)[0]
                header_size = 16
            elif size == 0:
                size = total - offset
            if size < header_size or offset + size > total:
                raise ValueError('MP4 顶层 box 长度无效')
            if kind == b'moof':
                fragmented = True
            if kind == b'moov':
                if found is not None or size > MAX_MOOV_BYTES:
                    raise ValueError('MP4 moov 重复或超出处理大小上限')
                found = (offset, size, source.read(size - header_size))
            offset += size
    if found is None:
        raise ValueError('MP4 缺少 moov')
    if fragmented or any(kind == b'mvex' for _, kind, _ in boxes(found[2])):
        raise ValueError('当前时间戳修复只支持普通非分片 MP4')
    return found


def video_track(moov):
    tracks = [payload for _, kind, payload in boxes(moov)
              if kind == b'trak' and child(child(payload, b'mdia'), b'hdlr')[8:12] == b'vide']
    if len(tracks) != 1:
        raise ValueError('时间戳修复要求只有一路视频轨道')
    return tracks[0]


def check_edits(moov):
    track = video_track(moov)
    for _, kind, data in boxes(track):
        if kind == b'edts':
            edits = child(data, b'elst')
            if edits[0] not in (0, 1) or u32(edits, 4) != 1:
                raise ValueError('暂不支持多段或空白编辑时间轴的 MP4 修复')
            pos = 8
            if edits[0] == 1:
                _, media_time, rate, fraction = struct.unpack_from('>Qqhh', edits, pos)
            else:
                _, media_time, rate, fraction = struct.unpack_from('>Iihh', edits, pos)
            if media_time < 0 or rate != 1 or fraction != 0:
                raise ValueError('暂不支持空白或变速编辑时间轴的 MP4 修复')


def sample_tables(moov):
    track = video_track(moov)
    mdia = child(track, b'mdia')
    mdhd = child(mdia, b'mdhd')
    if mdhd[0] not in (0, 1):
        raise ValueError('不支持的 mdhd 版本')
    timescale = u32(mdhd, 20 if mdhd[0] == 1 else 12)
    if not timescale:
        raise ValueError('MP4 视频 timescale 为零')
    stbl = child(child(mdia, b'minf'), b'stbl')
    stsz = child(stbl, b'stsz')
    fixed_size, count = u32(stsz, 4), u32(stsz, 8)
    if not 0 < count <= MAX_SAMPLES:
        raise ValueError('MP4 帧数无效或超出处理上限')
    sizes = ([fixed_size] * count if fixed_size else
             list(struct.unpack_from(f'>{count}I', stsz, 12)))
    names = {kind: payload for _, kind, payload in boxes(stbl)}
    if b'co64' in names:
        chunks = struct.unpack_from(f'>{u32(names[b"co64"], 4)}Q', names[b'co64'], 8)
    else:
        chunks = struct.unpack_from(f'>{u32(names[b"stco"], 4)}I', names[b'stco'], 8)
    stsc = child(stbl, b'stsc')
    entries = [struct.unpack_from('>III', stsc, 8 + i * 12) for i in range(u32(stsc, 4))]
    if not entries or entries[0][0] != 1:
        raise ValueError('MP4 chunk 索引无效')
    positions = []
    sample = entry = 0
    for chunk_no, offset in enumerate(chunks, 1):
        while entry + 1 < len(entries) and entries[entry + 1][0] <= chunk_no:
            entry += 1
        for _ in range(entries[entry][1]):
            if sample >= count:
                raise ValueError('MP4 样本与 chunk 数量不一致')
            positions.append(offset)
            offset += sizes[sample]
            sample += 1
    if sample != count:
        raise ValueError('MP4 样本与 chunk 数量不一致')
    def expand(table, signed=False):
        values = []
        fmt = '>Ii' if signed else '>II'
        for i in range(u32(table, 4)):
            n, value = struct.unpack_from(fmt, table, 8 + i * 8)
            if not n or len(values) + n > count:
                raise ValueError('MP4 时间表条目数量无效')
            values.extend([value] * n)
        if len(values) != count:
            raise ValueError('MP4 时间表与帧数不一致')
        return values
    durations = expand(child(stbl, b'stts'))
    if min(durations) <= 0:
        raise ValueError('MP4 存在非正帧时长，不能可靠恢复显示时序')
    ctts = names.get(b'ctts')
    if ctts is not None and ctts[0] not in (0, 1):
        raise ValueError('不支持的 ctts 版本')
    offsets = expand(ctts, ctts[0] == 1) if ctts is not None else [0] * count
    dts = []
    timestamp = 0
    for duration in durations:
        dts.append(timestamp)
        timestamp += duration
    return track, positions, durations, dts, offsets


class MP4StreamTimestampRepair:
    """解码器有界地提供显示顺序，流复制分片在发送前补写 trun 显示偏移。"""
    def __init__(self, source):
        self.source = source
        moov = read_moov(source)[2]
        check_edits(moov)
        track, self.positions, self.durations, self.dts, self.cts = sample_tables(moov)
        self.position_index = {pos: i for i, pos in enumerate(self.positions)}
        mdia = child(track, b'mdia')
        mdhd = child(mdia, b'mdhd')
        self.timescale = u32(mdhd, 20 if mdhd[0] == 1 else 12)
        stbl = child(child(mdia, b'minf'), b'stbl')
        stsz = child(stbl, b'stsz')
        self.sizes = ([u32(stsz, 4)] * len(self.positions) if u32(stsz, 4) else
                      list(struct.unpack_from(f'>{len(self.positions)}I', stsz, 12)))
        stss = next((data for _, kind, data in boxes(stbl) if kind == b'stss'), None)
        self.keys = ([n - 1 for n in struct.unpack_from(f'>{u32(stss, 4)}I', stss, 8)]
                     if stss is not None else list(range(len(self.positions))))
        if not self.keys or any(n < 0 or n >= len(self.positions) for n in self.keys):
            raise ValueError('MP4 关键帧样本索引无效')
        self.vfr = max(self.durations) - min(self.durations) > 1
        # 构造函数在线程池中读取元数据；Python 3.8 的 Queue 必须在事件循环线程创建。
        self.queue = None
        self.pending = {}
        self.process = self.reader = None
        self.error = None
        self.track_id = self.output_timescale = self.base_dts = None
        self.cursor = self.start_sample = 0
        self.last_pts = None
        self.started = False
        self.close_task = None

    async def start(self, ffmpeg, seconds):
        self.queue = asyncio.Queue(maxsize=128)
        self.seek_time = seconds
        command = [ffmpeg, '-hide_banner', '-nostdin', '-nostats', '-threads', '1',
                   '-ignore_editlist', '1', '-noaccurate_seek']
        if seconds > 0:
            command += ['-ss', f'{seconds:.9f}']
        command += ['-i', self.source, '-map', '0:v:0', '-an', '-sn', '-dn',
                    '-vf', 'scale=1:1,showinfo', '-vsync', '0', '-f', 'null', 'pipe:1']
        self.process = await asyncio.create_subprocess_exec(*command,
            stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        async def read_frames():
            tail = []
            try:
                while line := await self.process.stderr.readline():
                    text = line.decode('utf-8', errors='replace')
                    tail.append(text)
                    tail[:] = tail[-10:]
                    match = re.search(r'\bn:\s*(\d+).*?\bpos:\s*(-?\d+)', text)
                    if not match:
                        continue
                    number, position = map(int, match.groups())
                    index = self.position_index.get(position)
                    if index is None or index < self.start_sample:
                        raise ValueError('无法把解码帧映射到请求范围内的 MP4 样本')
                    if self.vfr:
                        pts = self.dts[index] + self.cts[index]
                        if self.last_pts is not None and pts <= self.last_pts:
                            raise ValueError('变帧率显示时序已异常，缺少可靠输出时序信息，不能按平均帧率修复')
                        self.last_pts = pts
                    await self.queue.put((number, index))
                code = await self.process.wait()
                if code:
                    raise ValueError('FFmpeg 显示顺序解码失败：' + ''.join(tail)[-1500:])
            except asyncio.CancelledError:
                # 取消时直接退出，避免满队列上的结束标记写入阻塞回收。
                raise
            except Exception as error:
                self.error = error
            # 正常结束和解码错误都通知消费者；此处等待同样允许被取消。
            await self.queue.put(None)
        self.reader = asyncio.create_task(read_frames())
        first = await self.next_frame()
        if first is None:
            raise self.error or ValueError('无法取得请求位置的首个显示帧')
        number, index = first
        if number != 0 or index not in self.keys:
            raise ValueError('流式修复未从关键帧开始')
        self.cursor = self.start_sample = index
        self.pending[index] = 0
        return self.dts[index] / self.timescale

    def init_segment(self, payload):
        moov = child(payload, b'moov')
        track = video_track(moov)
        tkhd = child(track, b'tkhd')
        self.track_id = u32(tkhd, 20 if tkhd[0] == 1 else 12)
        mdhd = child(child(track, b'mdia'), b'mdhd')
        self.output_timescale = u32(mdhd, 20 if mdhd[0] == 1 else 12)

    async def next_frame(self):
        """等待一条显示帧记录，同时可靠传递 Python 3.8 下的外部取消。"""
        reader = asyncio.create_task(self.queue.get())
        try:
            # 避免旧版 wait_for 在子任务刚完成时吞掉外部取消的竞争条件。
            done, _ = await asyncio.wait({reader}, timeout=30)
            if not done:
                raise asyncio.TimeoutError()
            return reader.result()
        finally:
            if not reader.done():
                reader.cancel()
            await asyncio.gather(reader, return_exceptions=True)

    async def display_number(self, index):
        while index not in self.pending:
            frame = await self.next_frame()
            if frame is None:
                raise self.error or ValueError('显示顺序解码提前结束，无法修复当前分片')
            number, sample = frame
            if number == 0 and sample != self.start_sample:
                raise ValueError('解码与流复制的起始关键帧不一致')
            if sample in self.pending:
                raise ValueError('解码器输出了重复样本')
            self.pending[sample] = number
            if len(self.pending) > 4096:
                raise ValueError('视频重排范围超出流式修复上限')
        return self.pending.pop(index)

    async def repair_segment(self, payload):
        moof = child(payload, b'moof')
        replacements = {}
        for traf_offset, kind, traf in boxes(moof):
            if kind != b'traf':
                continue
            tfhd = child(traf, b'tfhd')
            flags = u32(tfhd) & 0xffffff
            if flags & 1 or not flags & 0x020000:
                raise ValueError('流式修复要求 fMP4 使用 moof 相对数据偏移')
            if u32(tfhd, 4) != self.track_id:
                continue
            p = 8 + (4 if flags & 2 else 0)
            default_duration = u32(tfhd, p) if flags & 8 else 0
            p += 4 if flags & 8 else 0
            default_size = u32(tfhd, p) if flags & 16 else 0
            tfdt = child(traf, b'tfdt')
            dts = struct.unpack_from('>Q' if tfdt[0] == 1 else '>I', tfdt, 4)[0]
            if self.base_dts is None:
                self.base_dts = dts
            for run_offset, run_kind, run in boxes(traf):
                if run_kind != b'trun':
                    continue
                run_flags = u32(run) & 0xffffff
                count = u32(run, 4)
                p = 8 + (4 if run_flags & 1 else 0) + (4 if run_flags & 4 else 0)
                result = bytearray(bytes([1]) + ((run_flags | 0x800).to_bytes(3, 'big')) + run[4:p])
                for _ in range(count):
                    if self.cursor >= len(self.positions):
                        raise ValueError('输出视频样本数超出原 MP4 范围')
                    begin = p
                    duration = u32(run, p) if run_flags & 0x100 else default_duration
                    p += 4 if run_flags & 0x100 else 0
                    size = u32(run, p) if run_flags & 0x200 else default_size
                    p += 4 if run_flags & 0x200 else 0
                    p += 4 if run_flags & 0x400 else 0
                    result.extend(run[begin:p])
                    p += 4 if run_flags & 0x800 else 0
                    if not duration or size != self.sizes[self.cursor]:
                        raise ValueError('流复制样本与原视频时间表不一致')
                    if not self.started:
                        if not run_flags & 1:
                            raise ValueError('首个视频 trun 缺少数据偏移')
                        moof_offset = next(pos for pos, kind, _ in boxes(payload) if kind == b'moof')
                        data_offset = moof_offset + struct.unpack_from('>i', run, 8)[0]
                        sample_position = self.positions[self.cursor]
                        def read_original_sample():
                            with open(self.source, 'rb') as source:
                                source.seek(sample_position)
                                return source.read(size)
                        original = await run_in_thread(read_original_sample)
                        if payload[data_offset:data_offset + size] != original:
                            raise ValueError('流复制与解码器未从同一个视频样本开始')
                        self.started = True
                    number = await self.display_number(self.cursor)
                    if self.vfr:
                        source_pts = self.dts[self.cursor] + self.cts[self.cursor]
                    else:
                        display_index = self.start_sample + number
                        if display_index >= len(self.dts):
                            raise ValueError('显示帧编号超出原 MP4 时间表')
                        source_pts = self.dts[display_index]
                    delta = source_pts - self.dts[self.start_sample]
                    target_pts = self.base_dts + (delta * self.output_timescale + self.timescale // 2) // self.timescale
                    offset = target_pts - dts
                    if not -(2**31) <= offset < 2**31:
                        raise ValueError('显示时间偏移超出 trun 范围')
                    result.extend(struct.pack('>i', offset))
                    dts += duration
                    self.cursor += 1
                if p != len(run):
                    raise ValueError('fMP4 trun 样本表长度无效')
                replacements[(traf_offset, run_offset)] = bytes(result)
        if not replacements:
            return payload
        def rewrite(delta):
            output = []
            for traf_offset, kind, data in boxes(moof):
                if kind == b'traf':
                    children = []
                    for run_offset, run_kind, run in boxes(data):
                        run = replacements.get((traf_offset, run_offset), run)
                        if run_kind == b'trun' and u32(run) & 1:
                            run = bytearray(run)
                            struct.pack_into('>i', run, 8, struct.unpack_from('>i', run, 8)[0] + delta)
                        children.append(box(run_kind, run))
                    data = b''.join(children)
                output.append(box(kind, data))
            return box(b'moof', b''.join(output))
        provisional = rewrite(0)
        delta = len(provisional) - len(moof) - 8
        repaired = rewrite(delta)
        return b''.join(repaired if kind == b'moof' else box(kind, data)
                        for _, kind, data in boxes(payload))

    def request_stop(self):
        """先解除帧队列背压并终止写入者，再等待管道与任务退出。"""
        if self.reader:
            self.reader.cancel()
        if self.process and self.process.returncode is None:
            try:
                self.process.kill()
            except ProcessLookupError:
                pass

    async def close(self, trace=None):
        if self.close_task is None:
            self.request_stop()
            self.close_task = asyncio.create_task(self._close(trace))
        # 重复取消播放任务时，不把取消继续传给进程回收任务。
        await asyncio.shield(self.close_task)

    async def _close(self, trace):
        #[DEBUG-START]
        if trace:
            trace.step('辅助解码读取任务开始回收', pid=self.process.pid if self.process else None,
                       queuedFrames=self.queue.qsize() if self.queue is not None else 0)
        #[DEBUG-END]
        if self.reader:
            await asyncio.gather(self.reader, return_exceptions=True)
        #[DEBUG-START]
        if trace:
            trace.step('辅助解码读取任务回收完成')
        #[DEBUG-END]
        if self.process:
            # returncode 已设置也不代表 PIPE 已排空，必须继续读取至 EOF。
            while await self.process.stderr.read(65536):
                pass
            #[DEBUG-START]
            if trace:
                trace.step('辅助解码 stderr 排空完成', returncode=self.process.returncode)
            #[DEBUG-END]
            await self.process.wait()
        #[DEBUG-START]
        if trace:
            trace.step('辅助解码进程回收完成')
        #[DEBUG-END]

