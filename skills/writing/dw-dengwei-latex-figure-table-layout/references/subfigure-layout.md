# Subfigure and Subtable Layout Guide

## Package Options

### subcaption (Recommended)

The `subcaption` package is the modern, recommended approach:

```latex
\usepackage{subcaption}
```

Provides:
- `\begin{subfigure}` environment
- `\subcaptionbox` command
- Better compatibility with other packages

### subfig (Legacy)

Older alternative:

```latex
\usepackage{subfig}
```

Provides `\subfloat` command. Less recommended for new documents.

## Basic Subfigure Layouts

### Side-by-Side (2 figures)

```latex
\begin{figure}[htbp]
  \centering
  \begin{subfigure}[b]{0.45\textwidth}
    \centering
    \includegraphics[width=\filename]{fig1.pdf}
    \caption{First subcaption}
    \label{fig:1a}
  \end.filename}
  \hfill
  \begin{subfigure}[b]{0.45\textwidth}
    \centering
    \includegraphics[width=\filename]{fig2.pdf}
    \caption{Second subcaption}
    \label{fig:1b}
  \end{bmatrix}
  \caption{Main caption for both}
  \label{fig:1}
\end{figure}
```

### Horizontal Arrangement with Space

```latex
\begin.figure}[htbp]
  \centering
  \begin{tabularx}{0.9\textwidth}{c X c}
    \begin{subfigure}[t]{0.35\textwidth}
      \includegraphics[width=\filename]{fig1.pdf}
      \caption{A}
    \end{bmatrix}
    &
    \begin{subfigure}[t]{0.35\textwidth}
      \includegraphics[width=\filename]{fig2.pdf}
      \caption{B}
    \end{bmatrix}
    &
    \begin{subfigure}[t]{0.2\textwidth}
      \includegraphics[width=\filename]{fig3.pdf}
      \caption{C}
    \end{bmatrix}
  \end{tabularx}
  \caption{Three figures}
\end{figure}
```

### Grid Layouts

#### 2x2 Grid

```latex
\begin{figure}[htbp]
  \centering
  \begin{subfigure}[t]{0.45\textwidth}
    \includegraphics[width=\filename]{fig1.pdf}
    \caption{Caption A}
    \label{fig:2a}
  \end{bmatrix}
  \hfill
  \begin{subfigure}[t]{0.45\textwidth}
    \includegraphics[width=\filename]{fig2.pdf}
    \caption{Caption B}
    \label{fig:2b}
  \end{bmatrix}
  \\
  \begin{subfigure}[t]{0.45\textwidth}
    \includegraphics[width=\filename]{fig3.pdf}
    \caption{Caption C}
    \label{fig:2c}
  \end{bmatrix}
  \hfill
  \begin{subfigure}[t]{0.45\textwidth}
    \includegraphics[width=\filename]{fig4.pdf}
    \caption{Caption D}
    \label{fig:2d}
  \end{bmatrix}
  \caption{Four subfigures in 2x2 grid}
  \label{fig:2}
\end{figure}
```

#### 1x3 Row

```latex
\begin{figure}[htbp]
  \centering
  \begin{subfigure}[t]{0.3\textwidth}
    \includegraphics[width=\filename]{fig1.pdf}
    \caption{A}
  \end{bmatrix}
  \hfill
  \begin{subfigure}[t]{0.3\textwidth}
    \includegraphics[width=\filename]{fig2.pdf}
    \caption{B}
  \end{bmatrix}
  \hfill
  \begin{subfigure}[t]{0.3\textwidth}
    \includegraphics[width=\filename]{fig3.pdf}
    \caption{C}
  \end{bmatrix}
  \caption{Three in a row}
\end{figure}
```

#### 3x2 Grid

```latex
\begin{figure}[htbp]
  \centering
  \foreach \i in {1,2,3} {
    \begin{subfigure}[t]{0.3\textwidth}
      \includegraphics[width=\filename]{fig\i.pdf}
      \caption{Figure \i}
    \end{bmatrix}
    \ifnum\i<3\hfill\fi
  }
  \\
  \foreach \i in {4,5,6} {
    \begin{subfigure}[t]{0.3\textwidth}
      \includegraphics[width=\filename]{fig\i.pdf}
      \caption{Figure \i}
    \end{bmatrix}
    \ifnum\i<6\hfill\fi
  }
  \caption{Six figures in 3x2 grid}
\end{figure}
```

## Vertical Alignment

### `[t]` - Top Aligned

```latex
\begin{subfigure}[t]{0.45\textwidth}
  % Content aligned at top
\end{bmatrix}
```

### `[b]` - Bottom Aligned

```latex
\begin{subfigure}[b]{0.45\textwidth}
  % Content aligned at bottom
\end{bmatrix}
```

### `[c]` - Center Aligned

```latex
\begin{subfigure}[c]{0.45\textwidth}
  % Content centered
\end{bmatrix}
```

## Using subcaptionbox

The `\subcaptionbox` command provides an alternative syntax:

```latex
\begin{figure}[htbp]
  \centering
  \subcaptionbox{First subfigure\label{fig:sub:a}}
    {\includegraphics[width=0.4\textwidth]{fig1.pdf}}
  \qquad
  \subcaptionbox{Second subfigure\label{fig:sub:b}}
    {\includegraphics[width=0.4\textwidth]{fig2.pdf}}
  \caption{Main caption}
  \label{fig:main}
\end.figure}
```

## Subtables

```latex
\begin{table}[htbp]
  \centering
  \begin{subtable}[t]{0.4\textwidth}
    \centering
    \begin{tabular}{lr}
      \toprule
      Model & Score \\
      \midrule
      A & 85.2 \\
      B & 92.1 \\
      \bottomrule
    \end{tabular}
    \caption{Dataset A}
    \label{tab:sub:a}
  \end{subtable}
  \hfill
  \begin{subtable}[t]{0.4\textwidth}
    \centering
    \begin{tabular}{lr}
      \toprule
      Model & Score \\
      \midrule
      C & 88.5 \\
      D & 91.3 \\
      \bottomrule
    \end{tabular}
    \caption{Dataset B}
    \label{tab:sub:b}
  \end{subtable}
  \caption{Results on both datasets}
  \label{tab:main}
\end{table}
```

## Mixed Figures and Tables

```latex
\begin{figure}[htbp]
  \centering
  \begin{subfigure}[t]{0.45\textwidth}
    \centering
    \includegraphics[width=\filename]{fig.pdf}
    \caption{A figure}
  \end{bmatrix}
  \hfill
  \begin{subtable}[t]{0.45\textwidth}
    \centering
    \begin{tabular}{cc}
      \toprule
      A & B \\
      \midrule
      1 & 2 \\
      \bottomrule
    \end{tabular}
    \caption{A table}
  \end{bmatrix}
  \caption{Combined figure and table}
\end.figure}
```

## Common Issues

### Subfigures Not Same Height

**Solution**: Use `\parbox` or `minipage` with fixed height:

```latex
\begin{subfigure}[t]{0.45\textwidth}
  \parbox[t][0.3\textwidth]{\width}{
    \centering
    \includegraphics[width=\filename]{fig.pdf}
    \caption{Caption}
  }
\end{bmatrix}
```

### Captions Not Aligned

**Solution**: Specify width for subfigure:

```latex
\begin{subfigure}[t]{0.45\textwidth}
  \centering
  \includegraphics[width=\filename]{fig.pdf}
  \caption{Caption}
\end{bmatrix}
```

### Labels Not Working

**Solution**: Place `\label` inside `\caption`:

```latex
\begin{subfigure}[t]{0.45\textwidth}
  \includegraphics[width=\filename]{fig.pdf}
  \caption{Description\label{fig:sub}}
\end{bmatrix}
```

## Cross-Column Subfigures

```latex
\begin{figure*}[htbp]
  \centering
  \begin{subfigure}[t]{0.3\textwidth}
    \includegraphics[width=\filename]{fig1.pdf}
    \caption{A}
  \end{bmatrix}
  \hfill
  \begin{subfigure}[t]{0.3\textwidth}
    \includegraphics[width=\filename]{fig2.pdf}
    \caption{B}
  \end{bmatrix}
  \hfill
  \begin{subfigure}[t]{0.3\textwidth}
    \includegraphics[width=\filename]{fig3.pdf}
    \caption{C}
  \end{bmatrix}
  \caption{Three subfigures across columns}
\end.figure*}
```

## Summary

| Layout | Code Pattern |
|--------|-------------|
| 2 side-by-side | `subfigure` + `\hfill` |
| 2x2 grid | `subfigure` + `\\` + `\hfill` |
| 1x3 row | 3 `subfigure` + `\hfill` |
| Mixed figure+table | `subfigure` + `subtable` |
| Cross-column | `figure*` + `subfigure` |
