"""Generate original minimal PDF fixtures without a PDF-generation dependency."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tests/fixtures'


def pdf(commands):
    stream = ('\n'.join(commands) + '\n').encode('ascii')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1500 240] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'endstream',
    ]
    data = b'%PDF-1.4\n'
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(data)
    data += f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    data += f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    return data


def text(x, y, value):
    escaped = value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    return f'BT /F1 8 Tf {x} {y} Td ({escaped}) Tj ET'


def main():
    final = [text(20, 215, 'Original synthetic final standings fixture - fictional data')]
    for x in [20, 50, 210, 310, 350, 1480]:
        final.append(f'{x} 170 m {x} 195 l S')
    for y in [170, 195]:
        final.append(f'20 {y} m 1480 {y} l S')
    for x, label in [(24, 'Rank'), (54, 'Institution'), (214, 'Conference'), (314, 'Div'), (354, 'Points')]:
        final.append(text(x, 180, label))
    for rank, school, conf, y, total in [(1, 'Example State', 'Example East', 150, 150), (2, 'Example College', 'Example West', 130, 75)]:
        pairs = ['0', '0'] * 14
        if rank == 1:
            pairs[10:12] = ['1', '100']
        else:
            pairs[0:4] = ['17', '25', '-', 'x']
        tail = ['DI', str(total), *pairs, str(total-50), '20', '30']
        for x, value in [(24, str(rank)), (54, school), (214, conf)]:
            final.append(text(x, y, value))
        for i, value in enumerate(tail):
            final.append(text(314 + i * 32, y, value))
    fall = [text(20, 215, 'Original synthetic fall standings fixture - fictional data'),
            text(20, 190, 'W.CC M.CC W.FH FBS FB FCS FB W.SOC M.SOC W.VB M.WP'),
            text(20, 150, '1 Example State Example East DI 80 4 80 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'),
            text(20, 130, '2 Example College Example West DI 25 - x 0 0 0 0 0 0 0 0 17 25 0 0 0 0 0 0')]
    records = []
    for name, commands, period in [('synthetic_final.pdf', final, 'final'), ('synthetic_fall.pdf', fall, 'fall')]:
        content = pdf(commands)
        (OUT / name).write_bytes(content)
        records.append(dict(file='tests/fixtures/' + name, season='2024-25', period=period,
                            source_url='https://example.org/' + name,
                            sha256=hashlib.sha256(content).hexdigest()))
    (OUT / 'pdf_manifest.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
