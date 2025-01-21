
#define TEST

#ifdef TEST
int main(int argc, char** argv){
    printf("Hello");
    return 0;
}
#else
int main(int argc, char** argv){
    printf("Goodbye");
    return 1;
}
#endif
