\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{hepingjie_lessonplan}[2026/07/15 v1.0 Hepingjie No.1 Middle School lesson plan]

\LoadClass[UTF8,a4paper,zihao=-4,fontset=windows]{ctexart}

\RequirePackage{geometry}
\RequirePackage{tabularray}
\RequirePackage{xparse}
\RequirePackage{expl3}
\RequirePackage{ragged2e}
\RequirePackage{setspace}
\RequirePackage{xcolor}

\geometry{
  a4paper,
  top=18mm,
  bottom=15mm,
  left=18mm,
  right=18mm,
  headheight=0pt,
  headsep=0pt,
  footskip=0pt
}

\pagestyle{empty}
\setlength{\parindent}{2em}
\setlength{\parskip}{0pt}
\setstretch{1.15}
\setlength{\fboxsep}{0pt}

\ExplSyntaxOn
\tl_new:N \l_hp_topic_tl
\tl_new:N \l_hp_type_tl
\tl_new:N \l_hp_chapter_total_tl
\tl_new:N \l_hp_topic_hours_tl
\tl_new:N \l_hp_lesson_no_tl
\tl_new:N \l_hp_year_tl
\tl_new:N \l_hp_month_tl
\tl_new:N \l_hp_day_tl
\tl_new:N \l_hp_record_page_tl
\tl_new:N \l_hp_school_tl
\tl_new:N \l_hp_title_tl

\keys_define:nn { hp / lesson }
  {
    topic         .tl_set:N = \l_hp_topic_tl,
    type          .tl_set:N = \l_hp_type_tl,
    chapter-total .tl_set:N = \l_hp_chapter_total_tl,
    topic-hours   .tl_set:N = \l_hp_topic_hours_tl,
    lesson-no     .tl_set:N = \l_hp_lesson_no_tl,
    year          .tl_set:N = \l_hp_year_tl,
    month         .tl_set:N = \l_hp_month_tl,
    day           .tl_set:N = \l_hp_day_tl,
    record-page   .tl_set:N = \l_hp_record_page_tl,
    school        .tl_set:N = \l_hp_school_tl,
    title         .tl_set:N = \l_hp_title_tl,
  }

\tl_set:Nn \l_hp_school_tl { 北京市和平街第一中学 }
\tl_set:Nn \l_hp_title_tl  { 课时教学设计 }

\NewDocumentCommand{\lessonplansetup}{m}
  { \keys_set:nn { hp / lesson } { #1 } }

\cs_new:Npn \HPTopic         { \tl_use:N \l_hp_topic_tl }
\cs_new:Npn \HPType          { \tl_use:N \l_hp_type_tl }
\cs_new:Npn \HPChapterTotal { \tl_use:N \l_hp_chapter_total_tl }
\cs_new:Npn \HPTopicHours   { \tl_use:N \l_hp_topic_hours_tl }
\cs_new:Npn \HPLessonNo     { \tl_use:N \l_hp_lesson_no_tl }
\cs_new:Npn \HPYear          { \tl_use:N \l_hp_year_tl }
\cs_new:Npn \HPMonth         { \tl_use:N \l_hp_month_tl }
\cs_new:Npn \HPDay           { \tl_use:N \l_hp_day_tl }
\cs_new:Npn \HPRecordPage   { \tl_use:N \l_hp_record_page_tl }
\cs_new:Npn \HPSchool        { \tl_use:N \l_hp_school_tl }
\cs_new:Npn \HPTitle         { \tl_use:N \l_hp_title_tl }
\ExplSyntaxOff

\newcommand{\HPFixedField}[2]{%
  \makebox[#1][c]{#2}%
}

\newcommand{\HPTwoLine}[2]{%
  \begin{tabular}{@{}c@{}}#1\\[-0.1em]#2\end{tabular}%
}

\newcommand{\HPFourVertical}[4]{%
  \begin{tabular}{@{}c@{}}#1\\[2.7em]#2\\[2.7em]#3\\[2.7em]#4\end{tabular}%
}

\newcommand{\HPOverviewContent}[1]{%
  \parbox[t]{\linewidth}{\RaggedRight\zihao{-4}\setstretch{1.18}#1}%
}

\newcommand{\HPTeacherContent}[1]{%
  \parbox[t]{\linewidth}{\RaggedRight\zihao{-4}\setstretch{1.25}#1}%
}

\newcommand{\HPStudentContent}[1]{%
  \parbox[t]{\linewidth}{\RaggedRight\zihao{-4}\setstretch{1.25}#1}%
}

\newcommand{\HPTimeContent}[1]{%
  \parbox[t]{\linewidth}{\centering\zihao{-4}\setstretch{1.25}#1}%
}

\newcommand{\HPReflectionContent}[1]{%
  \parbox[t]{\linewidth}{\RaggedRight\zihao{-4}\setstretch{1.25}#1}%
}

\NewDocumentCommand{\LessonStage}{m m}{%
  \par\noindent{\heiti #1}\par
  #2\par\medskip
}

\NewDocumentCommand{\MakeLessonOverview}{m m m m m m}{%
  \begin{center}
    {\heiti\zihao{2}\HPSchool\HPTitle}\par
  \end{center}
  \vspace{7mm}
  \noindent\hspace{8mm}{\zihao{4}授课时间}\hspace{7mm}%
  \HPFixedField{14mm}{\HPYear}{\zihao{4}年}%
  \HPFixedField{12mm}{\HPMonth}{\zihao{4}月}%
  \HPFixedField{12mm}{\HPDay}{\zihao{4}日}%
  \hfill{\zihao{4}第}\HPFixedField{12mm}{\HPRecordPage}{\zihao{4}页}\hspace{8mm}
  \vspace{4mm}

  \noindent\begin{tblr}{
    width=\textwidth,
    colspec={*{12}{X[c,m]}},
    rows={rowsep=0pt},
    columns={colsep=1.2mm},
    hlines={0.45pt},
    vlines={0.45pt},
    row{1}={ht=10mm},
    row{2}={ht=10mm},
    row{3}={ht=42mm},
    row{4}={ht=18mm},
    row{5}={ht=18mm},
    row{6}={ht=18mm},
    row{7}={ht=18mm},
    row{8}={ht=80mm},
    cells={font=\songti\zihao{-4}},
  }
    课题 & \SetCell[c=7]{l}\HPTopic & & & & & & & 课型 & \SetCell[c=3]{l}\HPType & & \\
    \SetCell[c=2]{c}章（单元）总课时 & & \SetCell[c=2]{c}\HPChapterTotal & &
    \SetCell[c=2]{c}本课题课时 & & \SetCell[c=2]{c}\HPTopicHours & &
    \SetCell[c=2]{c}本节课是第 & & \SetCell[c=2]{c}\HPLessonNo\;课时 & \\
    \HPTwoLine{教学}{目标} & \SetCell[c=11]{l,t}\HPOverviewContent{#1} & & & & & & & & & & \\
    \HPTwoLine{教学}{重点} & \SetCell[c=11]{l,t}\HPOverviewContent{#2} & & & & & & & & & & \\
    \HPTwoLine{教学}{难点} & \SetCell[c=11]{l,t}\HPOverviewContent{#3} & & & & & & & & & & \\
    \HPTwoLine{教学}{方法} & \SetCell[c=11]{l,t}\HPOverviewContent{#4} & & & & & & & & & & \\
    \HPTwoLine{教学}{手段} & \SetCell[c=11]{l,t}\HPOverviewContent{#5} & & & & & & & & & & \\
    \HPTwoLine{板书}{设计} & \SetCell[c=11]{l,t}\HPOverviewContent{#6} & & & & & & & & & & \\
  \end{tblr}
  \clearpage
}

\NewDocumentCommand{\MakeTeachingProcessPage}{m m m}{%
  \noindent\begin{tblr}{
    width=\textwidth,
    colspec={Q[c,m,wd=12mm] X[l,t] Q[l,t,wd=29mm] Q[c,t,wd=15mm]},
    rows={rowsep=0pt},
    columns={colsep=1.4mm},
    hlines={0.45pt},
    vlines={0.45pt},
    row{1}={ht=9mm},
    row{2}={ht=247mm},
    cells={font=\songti\zihao{-4}},
  }
    \SetCell[c=2]{c}教师教学活动设计 & & 学生活动 & 估时 \\
    \HPFourVertical{教}{学}{过}{程} & \HPTeacherContent{#1} & \HPStudentContent{#2} & \HPTimeContent{#3} \\
  \end{tblr}
  \clearpage
}

\NewDocumentCommand{\MakeTeachingProcessReflectionPage}{m m m m}{%
  \noindent\begin{tblr}{
    width=\textwidth,
    colspec={Q[c,m,wd=12mm] X[l,t] Q[l,t,wd=29mm] Q[c,t,wd=15mm]},
    rows={rowsep=0pt},
    columns={colsep=1.4mm},
    hlines={0.45pt},
    vlines={0.45pt},
    row{1}={ht=9mm},
    row{2}={ht=168mm},
    row{3}={ht=70mm},
    cells={font=\songti\zihao{-4}},
  }
    \SetCell[c=2]{c}教师教学活动设计 & & 学生活动 & 估时 \\
    \HPFourVertical{教}{学}{过}{程} & \HPTeacherContent{#1} & \HPStudentContent{#2} & \HPTimeContent{#3} \\
    \HPFourVertical{课}{后}{反}{思} & \SetCell[c=3]{l,t}\HPReflectionContent{#4} & & \\
  \end{tblr}
}

\endinput
