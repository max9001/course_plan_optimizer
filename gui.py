import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from src.planner import CoursePlanner
from src.scraper import scape_read_csv
from src.utils import *


COURSE_DATA_PATH = 'data\courses.csv'
AVAILABILITY_DATA_PATH = 'data\course_avail.csv'

st.set_page_config(
    page_title='UCI Course Planner',
    page_icon='📚',
    layout='wide',
    initial_sidebar_state='auto'
)
tab1, tab2, tab3 = st.tabs(['Home', 'Course Planner', 'About'])


@st.cache_data
def load_courses(path: str) -> dict:
    df = pd.read_csv(path)
    course_dict = {}
    for _, row in df.iterrows():
        course_id = row['CoursesID']
        title = row['Title']
        prereq = row['Prerequisites']
        units = row['Units']
        prereq_list = [] if pd.isnull(prereq) else prereq.split('+')
        course_dict[course_id] = (title, prereq_list, units)
    return course_dict


@st.cache_data
def load_availability(path: str) -> dict:
    return scape_read_csv(path)


with st.sidebar:
    st.sidebar.title('Major')
    major = st.sidebar.selectbox(
        'Select your major', 
        ['Software Engineering', 'Computer Science', 'Data Science', 'Informatics']
    )

    st.sidebar.title('Start Year')
    start_year = st.sidebar.text_input('Enter your start year', '2023')

    st.sidebar.title('Planned Years')
    st.session_state['planned_years'] = st.sidebar.slider('How many years do you plan to take?', 1, 6, 2)

    st.sidebar.title('Max Units per Semester')
    max_units = st.sidebar.slider('How many units do you plan to take per semester?', 1, 20, 16)

    st.sidebar.title('Completed Courses')
    completed_courses = st.sidebar.multiselect(
        'Select the courses you have already completed/are going to transfer over',
        [k for k, (_, _, _) in load_courses(COURSE_DATA_PATH).items()],
    )

    st.session_state['student_plan'] = CoursePlanner(
        data_path=COURSE_DATA_PATH,
        planned_years=st.session_state['planned_years'],
        max_courses_per_sem=4,
        completed_courses=completed_courses,
    )
    
    st.subheader(f'Course Information for {major}')
    st.dataframe(pd.read_csv('data\courses.csv'), hide_index=True)


with tab1:
    st.title('UCI Course Plan Optimizer')
    st.write('This is a course planner for UCI students. It is designed to help students plan out their courses for the next few years.')
    st.write('This app will create the optimal academic year plan for students. This tool uses Bayesian networks, DFS, Topological sorting to build DAGs that prevent class conflicts, considering prerequisites, corequisites, units & course likeness. Streamline your course planning with ease. GitHub repo for efficient scheduling.')
    st.image('https://media.tenor.com/CYE3MnKr2nQAAAAd/dog-huh.gif')
    
    # st.subheader('Direct Acyclic Graphs')
    # st.write('The following is the prerequisite DAG for the major courses')
    # graph_relationship(
    #     {k: v[1] for k, v in load_courses(COURSE_DATA_PATH).items()},
    # )


with tab2:
    availability_list = load_availability(AVAILABILITY_DATA_PATH)
    courses_avail = {k: availability_list[k] for k, _ in st.session_state['student_plan'].course_dict.items()}
    courses_avail = {k: v for k, v in sorted(courses_avail.items(), key=lambda item: len(item[1]))}

    session = {
        f'{s}{i}': [] 
            for i in range(st.session_state['planned_years'])
            for s in ['Fall', 'Winter', 'Spring'] 
    }

    st.subheader('Add fixed Core Courses')
    for i in range(st.session_state['planned_years']):
        for season in ['Fall', 'Winter', 'Spring']:
            # Multiselect for each season
            st.write(f'**{season} {i}**')
            session[f'{season}{i}'] = st.multiselect(
                'Select the courses you want to take this season',
                [k for k, v in courses_avail.items() if season in v],
                key=f'{season}{i}'
            )


    if st.button('Generate Plan'):
        for i in range(st.session_state['planned_years']):
            for season in ['Fall', 'Winter', 'Spring']:
                if f'{season}{i}' in st.session_state:
                    st.session_state['student_plan'].fixed_core_course(
                        f'{season}{i}',
                        session[f'{season}{i}']
                    )

        st.session_state['student_plan'].build_plan(courses_avail) 
        st.subheader('Potential Plan')
        schedule = st.session_state['student_plan'].schedule
        st.table(schedule)