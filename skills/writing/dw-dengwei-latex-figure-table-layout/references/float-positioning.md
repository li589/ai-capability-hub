# Float Positioning Guide

## Understanding LaTeX Float Algorithm

LaTeX uses an algorithm to place floats (figures and tables) with the goal of:
1. Keeping floats near their reference in the text
2. Preventing floats from disrupting page layout
3. Filling pages efficiently

## Position Specifiers Explained

### `[h]` - Here
Places the float exactly where it appears in the source code.
- **Warning**: If the float doesn't fit, LaTeX may ignore this and use other positions
- Avoid using alone: `[h]` alone often causes floats to drift

### `[t]` - Top
Places the float at the top of the current or next page.

### `[b]` - Bottom
Places the float at the bottom of the current or next page.

### `[p]` - Page of Floats
Creates a separate page containing only floats.

### `[!]` - Override
Overrides some of LaTeX's float placement restrictions.

## Combination Order Matters

```latex
\begin{figure}[htbp]  % Order of preference
```

LaTeX will try positions in this order:
1. `h` - Here
2. `t` - Top
3. `b` - Bottom
4. `p` - Float page

## Common Problems

### Float at End of Document

**Problem**: Figures appear after all text, near references.

**Cause**: Using `[h]` when the float cannot fit.

**Solution**:
```latex
% Change from:
\begin{figure}[h]

% To:
\begin{figure}[htbp]
% Or:
\begin{figure}[!htbp]
```

### Float Takes Entire Page

**Problem**: A single figure occupies a whole page.

**Cause**: `[p]` creates a float page when no other position works.

**Solution**:
```latex
% Remove p from specifier
\begin{figure}[htb]
```

### Float Placement Too Late

**Problem**: Figure 2 appears after Section 3.

**Cause**: LaTeX's float algorithm.

**Solutions**:
1. Move float closer to its reference in source
2. Use `[!htbp]` to force placement
3. Use `\FloatBarrier` from `placeins`:
```latex
\usepackage{placeins}
\section{Section}
See \figureref{fig:myfig}.

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{fig.pdf}
  \caption{My figure}
  \label{fig:myfig}
\end{figure}
\FloatBarrier
```

## Package: placeins

The `placeins` package provides `\FloatBarrier` to prevent floats from crossing a point:

```latex
\usepackage{placeins}

\section{Section Title}
Some text.

\FloatBarrier  % No floats will cross this line

\begin{figure}[htbp]
  % Figure will stay above this barrier
\end{figure}
```

## Package: flafter

The `flafter` package ensures floats never appear before their definition:

```latex
\usepackage{flafter}

\section{Section}
As shown in \figureref{fig:future}, ...

\begin{figure}[htbp]
  % This figure will always appear after this point
  % even if placed "above" in source order
\endfigure}
```

## Float Parameters (Advanced)

You can adjust float behavior with `\makeatletter`:

```latex
\makeatletter
% Increase the fraction of page allowed for floats
renewcommand{\fraction}{0.7}

% Change total number of floats per page
renewcommand{\topnumber}{3}
renewcommand{\bottomnumber}{2}
\makeatother
```

## Cross-Column Documents

In twocolumn mode, use `figure*` and `table*`:

```latex
\begin{figure*}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{wide.pdf}
  \caption{Spans both columns}
\end{figure*}
```

Note: `[p]` in `figure*` creates a float page in the first column only.

## Summary Recommendations

| Situation | Recommended Specifier |
|-----------|----------------------|
| General use | `[htbp]` |
| Important figure | `[!htbp]` |
| Large figure at top | `[tb]` |
| Small figure here | `[ht]` |
| Many small figures | `[p]` |
